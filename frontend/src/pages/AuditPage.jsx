import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../components/ui/table';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../components/ui/dropdown-menu';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  RefreshCw,
  Shield,
  User,
  Zap,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Activity,
  Database,
  Lock
} from 'lucide-react';
import { motion } from 'framer-motion';

// Mock data - replace with real API calls
const mockAuditLogs = [
  {
    id: 1,
    timestamp: '2024-01-25 14:30:25',
    user_id: 1,
    username: 'admin',
    action: 'user_login',
    resource_type: 'authentication',
    resource_id: null,
    details: 'Successful login from IP 192.168.1.100',
    ip_address: '192.168.1.100',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'success',
    severity: 'info'
  },
  {
    id: 2,
    timestamp: '2024-01-25 14:25:12',
    user_id: 2,
    username: 'sarah.johnson',
    action: 'rule_created',
    resource_type: 'rule',
    resource_id: 15,
    details: 'Created new automation rule: "Auto-assign High Priority Tickets"',
    ip_address: '192.168.1.105',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    status: 'success',
    severity: 'info'
  },
  {
    id: 3,
    timestamp: '2024-01-25 14:20:45',
    user_id: 1,
    username: 'admin',
    action: 'user_created',
    resource_type: 'user',
    resource_id: 6,
    details: 'Created new user account: john.smith@company.com',
    ip_address: '192.168.1.100',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'success',
    severity: 'medium'
  },
  {
    id: 4,
    timestamp: '2024-01-25 14:15:33',
    user_id: 3,
    username: 'mike.chen',
    action: 'login_failed',
    resource_type: 'authentication',
    resource_id: null,
    details: 'Failed login attempt - invalid password',
    ip_address: '192.168.1.110',
    user_agent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
    status: 'failed',
    severity: 'warning'
  },
  {
    id: 5,
    timestamp: '2024-01-25 14:10:18',
    user_id: 2,
    username: 'sarah.johnson',
    action: 'integration_connected',
    resource_type: 'integration',
    resource_id: 3,
    details: 'Connected Slack integration: "Main Workspace"',
    ip_address: '192.168.1.105',
    user_agent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    status: 'success',
    severity: 'info'
  },
  {
    id: 6,
    timestamp: '2024-01-25 14:05:42',
    user_id: 1,
    username: 'admin',
    action: 'rule_executed',
    resource_type: 'rule',
    resource_id: 12,
    details: 'Executed rule: "Weekly Report Generation" - Success',
    ip_address: 'system',
    user_agent: 'SupportOps Automator v1.0',
    status: 'success',
    severity: 'info'
  },
  {
    id: 7,
    timestamp: '2024-01-25 14:00:15',
    user_id: 4,
    username: 'emma.davis',
    action: 'data_export',
    resource_type: 'audit',
    resource_id: null,
    details: 'Exported audit logs for compliance review',
    ip_address: '192.168.1.115',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'success',
    severity: 'high'
  },
  {
    id: 8,
    timestamp: '2024-01-25 13:55:28',
    user_id: 1,
    username: 'admin',
    action: 'security_setting_changed',
    resource_type: 'settings',
    resource_id: null,
    details: 'Updated password policy: minimum length increased to 12 characters',
    ip_address: '192.168.1.100',
    user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    status: 'success',
    severity: 'high'
  }
];

const getActionIcon = (action) => {
  switch (action) {
    case 'user_login':
    case 'login_failed':
      return <User className="h-4 w-4" />;
    case 'rule_created':
    case 'rule_executed':
    case 'rule_updated':
    case 'rule_deleted':
      return <Zap className="h-4 w-4" />;
    case 'integration_connected':
    case 'integration_disconnected':
      return <Activity className="h-4 w-4" />;
    case 'user_created':
    case 'user_updated':
    case 'user_deleted':
      return <User className="h-4 w-4" />;
    case 'data_export':
    case 'data_deletion':
      return <Database className="h-4 w-4" />;
    case 'security_setting_changed':
      return <Lock className="h-4 w-4" />;
    default:
      return <FileText className="h-4 w-4" />;
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'success':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'failed':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'warning':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getSeverityColor = (severity) => {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'medium':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'warning':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'info':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'success':
      return <CheckCircle className="h-3 w-3" />;
    case 'failed':
      return <XCircle className="h-3 w-3" />;
    case 'warning':
      return <AlertTriangle className="h-3 w-3" />;
    default:
      return <Clock className="h-3 w-3" />;
  }
};

const AuditLogRow = ({ log, onViewDetails }) => (
  <TableRow className="hover:bg-gray-50 dark:hover:bg-gray-800">
    <TableCell>
      <div className="text-sm font-mono text-gray-900 dark:text-white">
        {log.timestamp}
      </div>
    </TableCell>
    <TableCell>
      <div className="flex items-center space-x-2">
        <div className={`p-1 rounded ${getSeverityColor(log.severity)}`}>
          {getActionIcon(log.action)}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-900 dark:text-white">
            {log.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {log.resource_type}
          </p>
        </div>
      </div>
    </TableCell>
    <TableCell>
      <div className="text-sm text-gray-900 dark:text-white">
        {log.username}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        ID: {log.user_id}
      </div>
    </TableCell>
    <TableCell>
      <div className="max-w-xs truncate text-sm text-gray-900 dark:text-white">
        {log.details}
      </div>
    </TableCell>
    <TableCell>
      <div className="flex items-center space-x-2">
        <Badge variant="outline" className={getStatusColor(log.status)}>
          {getStatusIcon(log.status)}
          <span className="ml-1">{log.status}</span>
        </Badge>
        <Badge variant="outline" className={getSeverityColor(log.severity)}>
          {log.severity}
        </Badge>
      </div>
    </TableCell>
    <TableCell>
      <div className="text-sm text-gray-500 dark:text-gray-400">
        {log.ip_address}
      </div>
    </TableCell>
    <TableCell>
      <Button 
        variant="ghost" 
        size="sm"
        onClick={() => onViewDetails(log)}
      >
        <Eye className="h-4 w-4" />
      </Button>
    </TableCell>
  </TableRow>
);

export const AuditPage = () => {
  const [logs, setLogs] = useState(mockAuditLogs);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [dateRange, setDateRange] = useState('today');
  const [isLoading, setIsLoading] = useState(false);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.details.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         log.action.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesAction = actionFilter === 'all' || log.action === actionFilter;
    const matchesStatus = statusFilter === 'all' || log.status === statusFilter;
    const matchesSeverity = severityFilter === 'all' || log.severity === severityFilter;
    return matchesSearch && matchesAction && matchesStatus && matchesSeverity;
  });

  const handleRefresh = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    console.log('Exporting audit logs...');
  };

  const handleViewDetails = (log) => {
    console.log('View log details:', log);
    // TODO: Open details modal
  };

  const getStats = () => {
    const today = new Date().toISOString().split('T')[0];
    const todayLogs = logs.filter(log => log.timestamp.startsWith(today));
    
    return {
      total: logs.length,
      today: todayLogs.length,
      failed: logs.filter(log => log.status === 'failed').length,
      high_severity: logs.filter(log => log.severity === 'high').length
    };
  };

  const stats = getStats();

  const uniqueActions = [...new Set(logs.map(log => log.action))];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Audit Logs
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor system activities and security events for compliance
          </p>
        </div>
        <div className="flex space-x-2">
          <Button 
            onClick={handleRefresh} 
            disabled={isLoading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            onClick={handleExport}
            variant="outline"
            size="sm"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.total}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Total Events
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.today}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Today's Events
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <XCircle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.failed}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Failed Events
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5 text-orange-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.high_severity}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    High Severity
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Audit Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Security & Activity Logs</CardTitle>
              <CardDescription>
                Comprehensive audit trail of all system activities
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6 flex-wrap gap-2">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <Select value={actionFilter} onValueChange={setActionFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Action" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {uniqueActions.map(action => (
                  <SelectItem key={action} value={action}>
                    {action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Date Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">This Week</SelectItem>
                <SelectItem value="month">This Month</SelectItem>
                <SelectItem value="all">All Time</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>IP Address</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.length > 0 ? (
                  filteredLogs.map((log) => (
                    <AuditLogRow
                      key={log.id}
                      log={log}
                      onViewDetails={handleViewDetails}
                    />
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="flex flex-col items-center space-y-2">
                        <FileText className="h-8 w-8 text-gray-400" />
                        <p className="text-gray-500 dark:text-gray-400">
                          No audit logs found matching your filters
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {filteredLogs.length > 0 && (
            <div className="flex items-center justify-between mt-4 text-sm text-gray-500 dark:text-gray-400">
              <p>
                Showing {filteredLogs.length} of {logs.length} events
              </p>
              <p>
                Last updated: {new Date().toLocaleTimeString()}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

