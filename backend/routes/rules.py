"""
Rule management routes
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, update, and_, desc
from database import get_session
from models.rule import Rule, RuleCreate, RuleUpdate, RuleResponse, RuleStatus
from models.audit import AuditLogCreate, AuditAction
from models.user import User
from services.audit import AuditService
from services.rule_engine import rule_engine
from routes.auth import get_current_user
from middleware import rate_limit_by_user, get_remote_address
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", response_model=RuleResponse)
@rate_limit_by_user("20/minute")
def create_rule(
    rule_data: RuleCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Create a new automation rule
    """
    try:
        # Create new rule
        new_rule = Rule(
            user_id=current_user.id,
            name=rule_data.name,
            description=rule_data.description,
            trigger_platform=rule_data.trigger_platform,
            trigger_event=rule_data.trigger_event,
            trigger_conditions=rule_data.trigger_conditions,
            actions=rule_data.actions,
            max_executions_per_hour=rule_data.max_executions_per_hour,
            execution_timeout_seconds=rule_data.execution_timeout_seconds,
            status=RuleStatus.DRAFT,
            is_enabled=False  # Start disabled for safety
        )
        
        session.add(new_rule)
        session.commit()
        session.refresh(new_rule)
        
        # Log rule creation
        client_ip = get_remote_address(request)
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.RULE_CREATED,
                resource_type="rule",
                resource_id=str(new_rule.id),
                rule_id=new_rule.id,
                ip_address=client_ip,
                details={
                    "rule_name": new_rule.name,
                    "trigger_platform": new_rule.trigger_platform,
                    "trigger_event": new_rule.trigger_event,
                    "actions_count": len(new_rule.actions)
                }
            )
        )
        
        return RuleResponse(
            id=new_rule.id,
            name=new_rule.name,
            description=new_rule.description,
            status=new_rule.status,
            trigger_platform=new_rule.trigger_platform,
            trigger_event=new_rule.trigger_event,
            trigger_conditions=new_rule.trigger_conditions,
            actions=new_rule.actions,
            is_enabled=new_rule.is_enabled,
            max_executions_per_hour=new_rule.max_executions_per_hour,
            execution_timeout_seconds=new_rule.execution_timeout_seconds,
            execution_count=new_rule.execution_count,
            last_executed_at=new_rule.last_executed_at,
            last_execution_status=new_rule.last_execution_status,
            created_at=new_rule.created_at,
            updated_at=new_rule.updated_at
        )
        
    except Exception as e:
        logger.error(f"Rule creation error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule creation failed"
        )


@router.get("/", response_model=List[RuleResponse])
@rate_limit_by_user("30/minute")
def get_rules(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[RuleStatus] = None,
    platform: Optional[str] = None,
    enabled_only: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get user's automation rules
    """
    try:
        query = select(Rule).where(
            and_(
                Rule.user_id == current_user.id,
                Rule.deleted_at.is_(None)
            )
        )
        
        # Apply filters
        if status_filter:
            query = query.where(Rule.status == status_filter)
        
        if platform:
            query = query.where(Rule.trigger_platform == platform)
        
        if enabled_only is not None:
            query = query.where(Rule.is_enabled == enabled_only)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(Rule.created_at))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = session.execute(query)
        rules = result.scalars().all()
        
        return [
            RuleResponse(
                id=rule.id,
                name=rule.name,
                description=rule.description,
                status=rule.status,
                trigger_platform=rule.trigger_platform,
                trigger_event=rule.trigger_event,
                trigger_conditions=rule.trigger_conditions,
                actions=rule.actions,
                is_enabled=rule.is_enabled,
                max_executions_per_hour=rule.max_executions_per_hour,
                execution_timeout_seconds=rule.execution_timeout_seconds,
                execution_count=rule.execution_count,
                last_executed_at=rule.last_executed_at,
                last_execution_status=rule.last_execution_status,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            for rule in rules
        ]
        
    except Exception as e:
        logger.error(f"Get rules error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rules"
        )


@router.get("/{rule_id}", response_model=RuleResponse)
@rate_limit_by_user("30/minute")
def get_rule(
    rule_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a specific rule by ID
    """
    try:
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            status=rule.status,
            trigger_platform=rule.trigger_platform,
            trigger_event=rule.trigger_event,
            trigger_conditions=rule.trigger_conditions,
            actions=rule.actions,
            is_enabled=rule.is_enabled,
            max_executions_per_hour=rule.max_executions_per_hour,
            execution_timeout_seconds=rule.execution_timeout_seconds,
            execution_count=rule.execution_count,
            last_executed_at=rule.last_executed_at,
            last_execution_status=rule.last_execution_status,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get rule error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rule"
        )


@router.put("/{rule_id}", response_model=RuleResponse)
@rate_limit_by_user("20/minute")
def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Update an automation rule
    """
    try:
        # Get rule to update
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        # Store old values for audit
        old_values = {
            "name": rule.name,
            "description": rule.description,
            "status": rule.status.value,
            "is_enabled": rule.is_enabled,
            "trigger_conditions": rule.trigger_conditions,
            "actions": rule.actions
        }
        
        # Prepare update data
        update_data = {}
        
        if rule_data.name is not None:
            update_data["name"] = rule_data.name
        
        if rule_data.description is not None:
            update_data["description"] = rule_data.description
        
        if rule_data.status is not None:
            update_data["status"] = rule_data.status
        
        if rule_data.trigger_conditions is not None:
            update_data["trigger_conditions"] = rule_data.trigger_conditions
        
        if rule_data.actions is not None:
            update_data["actions"] = rule_data.actions
        
        if rule_data.is_enabled is not None:
            update_data["is_enabled"] = rule_data.is_enabled
        
        if rule_data.max_executions_per_hour is not None:
            update_data["max_executions_per_hour"] = rule_data.max_executions_per_hour
        
        if rule_data.execution_timeout_seconds is not None:
            update_data["execution_timeout_seconds"] = rule_data.execution_timeout_seconds
        
        # Update rule
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            session.execute(
                update(Rule).where(Rule.id == rule_id).values(**update_data)
            )
            session.commit()
            
            # Refresh rule object
            session.refresh(rule)
            
            # Log rule update
            client_ip = get_remote_address(request)
            new_values = {k: str(v) for k, v in update_data.items() if k != "updated_at"}
            
            AuditService.log_action(
                session,
                AuditLogCreate(
                    user_id=current_user.id,
                    username=current_user.username,
                    action=AuditAction.RULE_UPDATED,
                    resource_type="rule",
                    resource_id=str(rule_id),
                    rule_id=rule_id,
                    ip_address=client_ip,
                    old_values=old_values,
                    new_values=new_values,
                    details={"updated_by": current_user.username}
                )
            )
        
        return RuleResponse(
            id=rule.id,
            name=rule.name,
            description=rule.description,
            status=rule.status,
            trigger_platform=rule.trigger_platform,
            trigger_event=rule.trigger_event,
            trigger_conditions=rule.trigger_conditions,
            actions=rule.actions,
            is_enabled=rule.is_enabled,
            max_executions_per_hour=rule.max_executions_per_hour,
            execution_timeout_seconds=rule.execution_timeout_seconds,
            execution_count=rule.execution_count,
            last_executed_at=rule.last_executed_at,
            last_execution_status=rule.last_execution_status,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule update error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule update failed"
        )


@router.delete("/{rule_id}")
@rate_limit_by_user("20/minute")
def delete_rule(
    rule_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Delete a rule (soft delete)
    """
    try:
        # Get rule to delete
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        # Soft delete rule
        session.execute(
            update(Rule).where(Rule.id == rule_id).values(
                deleted_at=datetime.utcnow(),
                is_enabled=False
            )
        )
        session.commit()
        
        # Log rule deletion
        client_ip = get_remote_address(request)
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.RULE_DELETED,
                resource_type="rule",
                resource_id=str(rule_id),
                rule_id=rule_id,
                ip_address=client_ip,
                details={
                    "rule_name": rule.name,
                    "deletion_type": "soft_delete",
                    "deleted_by": current_user.username
                }
            )
        )
        
        return {"message": "Rule deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule deletion error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule deletion failed"
        )


@router.post("/{rule_id}/test")
@rate_limit_by_user("10/minute")
def test_rule(
    rule_id: int,
    test_payload: dict,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Test a rule with sample data
    """
    try:
        # Get rule
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        # Test rule
        test_result = rule_engine.test_rule(session, rule, test_payload)
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule test error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule test failed"
        )


@router.post("/{rule_id}/enable")
@rate_limit_by_user("10/minute")
def enable_rule(
    rule_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Enable a rule
    """
    try:
        # Get rule
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        # Enable rule
        session.execute(
            update(Rule).where(Rule.id == rule_id).values(
                is_enabled=True,
                status=RuleStatus.ACTIVE,
                updated_at=datetime.utcnow()
            )
        )
        session.commit()
        
        # Log rule enabling
        client_ip = get_remote_address(request)
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.RULE_UPDATED,
                resource_type="rule",
                resource_id=str(rule_id),
                rule_id=rule_id,
                ip_address=client_ip,
                details={
                    "action": "enabled",
                    "rule_name": rule.name
                }
            )
        )
        
        return {"message": "Rule enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule enable error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable rule"
        )


@router.post("/{rule_id}/disable")
@rate_limit_by_user("10/minute")
def disable_rule(
    rule_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Disable a rule
    """
    try:
        # Get rule
        result = session.execute(
            select(Rule).where(
                and_(
                    Rule.id == rule_id,
                    Rule.user_id == current_user.id,
                    Rule.deleted_at.is_(None)
                )
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rule not found"
            )
        
        # Disable rule
        session.execute(
            update(Rule).where(Rule.id == rule_id).values(
                is_enabled=False,
                status=RuleStatus.INACTIVE,
                updated_at=datetime.utcnow()
            )
        )
        session.commit()
        
        # Log rule disabling
        client_ip = get_remote_address(request)
        AuditService.log_action(
            session,
            AuditLogCreate(
                user_id=current_user.id,
                username=current_user.username,
                action=AuditAction.RULE_UPDATED,
                resource_type="rule",
                resource_id=str(rule_id),
                rule_id=rule_id,
                ip_address=client_ip,
                details={
                    "action": "disabled",
                    "rule_name": rule.name
                }
            )
        )
        
        return {"message": "Rule disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rule disable error: {e}")
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable rule"
        )

