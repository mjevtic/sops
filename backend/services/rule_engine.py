"""
Rule engine for processing automation workflows
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_
from models.rule import Rule, RuleStatus, RuleExecution
from models.audit import AuditLogCreate, AuditAction
from models.integration import Integration, IntegrationCredential
from services.audit import AuditService
from config import decrypt_data
import logging
import importlib

logger = logging.getLogger(__name__)


class RuleEngine:
    """Rule engine for processing automation workflows"""
    
    def __init__(self):
        self.execution_cache = {}  # Cache for ongoing executions
    
    def process_trigger(
        self,
        session: Session,
        platform: str,
        event: str,
        payload: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> List[str]:
        """
        Process incoming trigger and execute matching rules
        
        Returns list of execution IDs
        """
        try:
            if not request_id:
                request_id = str(uuid.uuid4())
            
            logger.info(f"Processing trigger: {platform}.{event} [{request_id}]")
            
            # Find matching rules
            matching_rules = self._find_matching_rules(
                session, platform, event, payload
            )
            
            if not matching_rules:
                logger.info(f"No matching rules found for {platform}.{event}")
                return []
            
            logger.info(f"Found {len(matching_rules)} matching rules")
            
            # Execute rules
            execution_ids = []
            for rule in matching_rules:
                execution_id = self._execute_rule(
                    session, rule, payload, request_id
                )
                if execution_id:
                    execution_ids.append(execution_id)
            
            return execution_ids
            
        except Exception as e:
            logger.error(f"Error processing trigger: {e}")
            raise
    
    def _find_matching_rules(
        self,
        session: Session,
        platform: str,
        event: str,
        payload: Dict[str, Any]
    ) -> List[Rule]:
        """Find rules that match the trigger"""
        try:
            # Get active rules for the platform and event
            result = session.execute(
                select(Rule).where(
                    and_(
                        Rule.trigger_platform == platform,
                        Rule.trigger_event == event,
                        Rule.status == RuleStatus.ACTIVE,
                        Rule.is_enabled == True,
                        Rule.deleted_at.is_(None)
                    )
                )
            )
            rules = result.scalars().all()
            
            matching_rules = []
            for rule in rules:
                if self._evaluate_conditions(rule, payload):
                    # Check rate limiting
                    if self._check_rate_limit(session, rule):
                        matching_rules.append(rule)
                    else:
                        logger.warning(f"Rate limit exceeded for rule {rule.id}")
            
            return matching_rules
            
        except Exception as e:
            logger.error(f"Error finding matching rules: {e}")
            return []
    
    def _evaluate_conditions(
        self,
        rule: Rule,
        payload: Dict[str, Any]
    ) -> bool:
        """Evaluate if rule conditions match the payload"""
        try:
            conditions = rule.trigger_conditions
            
            if not conditions:
                return True  # No conditions means always match
            
            # Simple condition evaluation
            for key, expected_value in conditions.items():
                if key not in payload:
                    return False
                
                actual_value = payload[key]
                
                # Handle different comparison types
                if isinstance(expected_value, dict):
                    operator = expected_value.get("operator", "equals")
                    value = expected_value.get("value")
                    
                    if operator == "equals":
                        if actual_value != value:
                            return False
                    elif operator == "contains":
                        if value not in str(actual_value):
                            return False
                    elif operator == "starts_with":
                        if not str(actual_value).startswith(str(value)):
                            return False
                    elif operator == "ends_with":
                        if not str(actual_value).endswith(str(value)):
                            return False
                    elif operator == "greater_than":
                        if not (isinstance(actual_value, (int, float)) and actual_value > value):
                            return False
                    elif operator == "less_than":
                        if not (isinstance(actual_value, (int, float)) and actual_value < value):
                            return False
                else:
                    # Simple equality check
                    if actual_value != expected_value:
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating conditions for rule {rule.id}: {e}")
            return False
    
    def _check_rate_limit(
        self,
        session: Session,
        rule: Rule
    ) -> bool:
        """Check if rule execution is within rate limits"""
        try:
            # Check executions in the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            # Count recent executions (this would be better with a separate executions table)
            if rule.last_executed_at and rule.last_executed_at > one_hour_ago:
                # Simple rate limiting based on execution count
                # In production, you'd want a more sophisticated approach
                if rule.execution_count >= rule.max_executions_per_hour:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for rule {rule.id}: {e}")
            return False
    
    def _execute_rule(
        self,
        session: Session,
        rule: Rule,
        trigger_data: Dict[str, Any],
        request_id: str
    ) -> Optional[str]:
        """Execute a single rule"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Executing rule {rule.id} [{execution_id}]")
            
            # Create execution record
            execution = RuleExecution(
                rule_id=rule.id,
                trigger_data=trigger_data,
                execution_id=execution_id,
                started_at=start_time,
                status="running"
            )
            
            # Store in cache
            self.execution_cache[execution_id] = execution
            
            # Execute actions
            actions_executed = []
            for action in rule.actions:
                try:
                    action_result = self._execute_action(
                        session, action, trigger_data, rule
                    )
                    actions_executed.append({
                        "action": action,
                        "result": action_result,
                        "status": "success"
                    })
                except Exception as e:
                    logger.error(f"Action execution failed: {e}")
                    actions_executed.append({
                        "action": action,
                        "error": str(e),
                        "status": "failed"
                    })
            
            # Update execution record
            execution.completed_at = datetime.utcnow()
            execution.status = "completed"
            execution.actions_executed = actions_executed
            
            # Update rule statistics
            session.execute(
                update(Rule).where(Rule.id == rule.id).values(
                    execution_count=rule.execution_count + 1,
                    last_executed_at=datetime.utcnow(),
                    last_execution_status="success"
                )
            )
            session.commit()
            
            # Log execution
            AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=rule.user_id,
                    action=AuditAction.RULE_EXECUTED,
                    resource_type="rule",
                    resource_id=str(rule.id),
                    rule_id=rule.id,
                    request_id=request_id,
                    details={
                        "execution_id": execution_id,
                        "trigger_platform": rule.trigger_platform,
                        "trigger_event": rule.trigger_event,
                        "actions_count": len(actions_executed),
                        "successful_actions": len([a for a in actions_executed if a["status"] == "success"])
                    },
                    duration_ms=int((execution.completed_at - start_time).total_seconds() * 1000)
                )
            )
            
            logger.info(f"Rule {rule.id} executed successfully [{execution_id}]")
            return execution_id
            
        except Exception as e:
            logger.error(f"Rule execution failed: {e}")
            
            # Update rule with error
            session.execute(
                update(Rule).where(Rule.id == rule.id).values(
                    last_execution_status="failed",
                    last_execution_error=str(e)
                )
            )
            session.commit()
            
            # Log execution failure
            AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=rule.user_id,
                    action=AuditAction.RULE_EXECUTION_FAILED,
                    resource_type="rule",
                    resource_id=str(rule.id),
                    rule_id=rule.id,
                    request_id=request_id,
                    details={
                        "execution_id": execution_id,
                        "error": str(e)
                    },
                    status="failed",
                    error_message=str(e)
                )
            )
            
            return None
        finally:
            # Clean up cache
            if execution_id in self.execution_cache:
                del self.execution_cache[execution_id]
    
    def _execute_action(
        self,
        session: Session,
        action: Dict[str, Any],
        trigger_data: Dict[str, Any],
        rule: Rule
    ) -> Dict[str, Any]:
        """Execute a single action"""
        try:
            platform = action.get("platform")
            action_type = action.get("type")
            
            if not platform or not action_type:
                raise ValueError("Action must have platform and type")
            
            logger.info(f"Executing action: {platform}.{action_type}")
            
            # Get integration credentials
            integration = self._get_integration(session, rule.user_id, platform)
            if not integration:
                raise ValueError(f"No integration found for platform: {platform}")
            
            # Load action module dynamically
            module_name = f"modules.{platform}.action"
            try:
                module = importlib.import_module(module_name)
                action_function = getattr(module, f"execute_{action_type}")
            except (ImportError, AttributeError) as e:
                raise ValueError(f"Action module not found: {module_name}.execute_{action_type}")
            
            # Decrypt credentials
            credentials = json.loads(decrypt_data(integration.credentials.encrypted_credentials))
            
            # Execute action
            result = action_function(
                credentials=credentials,
                action_config=action,
                trigger_data=trigger_data,
                integration_config=integration.config
            )
            
            # Update integration statistics
            session.execute(
                update(Integration).where(Integration.id == integration.id).values(
                    total_actions_executed=integration.total_actions_executed + 1,
                    last_action_executed_at=datetime.utcnow()
                )
            )
            session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Action execution error: {e}")
            raise
    
    def _get_integration(
        self,
        session: Session,
        user_id: int,
        platform: str
    ) -> Optional[Integration]:
        """Get user's integration for a platform"""
        try:
            result = session.execute(
                select(Integration).join(IntegrationCredential).where(
                    and_(
                        Integration.user_id == user_id,
                        Integration.platform == platform,
                        Integration.status == "active",
                        Integration.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting integration: {e}")
            return None
    
    def get_execution_status(self, execution_id: str) -> Optional[RuleExecution]:
        """Get execution status"""
        return self.execution_cache.get(execution_id)
    
    def test_rule(
        self,
        session: Session,
        rule: Rule,
        test_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test a rule with sample data"""
        try:
            logger.info(f"Testing rule {rule.id}")
            
            # Check if conditions match
            conditions_match = self._evaluate_test_conditions(rule, test_payload)
            
            if not conditions_match:
                return {
                    "status": "conditions_not_met",
                    "message": "Rule conditions do not match the test payload",
                    "conditions_match": False
                }
            
            # Simulate action execution (don't actually execute)
            simulated_actions = []
            for action in rule.actions:
                simulated_actions.append({
                    "platform": action.get("platform"),
                    "type": action.get("type"),
                    "config": action,
                    "status": "simulated"
                })
            
            return {
                "status": "success",
                "message": "Rule test completed successfully",
                "conditions_match": True,
                "actions_to_execute": simulated_actions,
                "test_payload": test_payload
            }
            
        except Exception as e:
            logger.error(f"Rule test error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "conditions_match": False
            }


# Global rule engine instance
rule_engine = RuleEngine()

