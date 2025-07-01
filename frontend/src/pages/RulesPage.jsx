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
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '../components/ui/dropdown-menu';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { 
  Zap, 
  Plus, 
  Search, 
  MoreHorizontal, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  Copy,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Filter
} from 'lucide-react';
import { motion } from 'framer-motion';

// Mock data - replace with real API calls
const mockRules = [
  {
    id: 1,
    name: 'Auto-assign High Priority Tickets',
    description: 'Automatically assign high priority tickets to senior support agents',
    trigger: 'Zendesk - Ticket Created',
    actions: ['Slack - Send Message', 'Trello - Create Card'],
    status: 'active',
    executions: 45,
    successRate: 97.8,
    lastExecuted: '2 minutes ago',
    created: '2024-01-15',
    priority: 'high'
  },
  {
    id: 2,
    name: 'Escalate Urgent Issues',
    description: 'Escalate urgent issues to management team',
    trigger: 'Freshdesk - Priority Changed',
    actions: ['Slack - Send DM', 'Notion - Create Page'],
    status: 'active',
    executions: 23,
    successRate: 100,
    lastExecuted: '15 minutes ago',
    created: '2024-01-10',
    priority: 'critical'
  },
  {
    id: 3,
    name: 'Weekly Report Generation',
    description: 'Generate and distribute weekly support reports',
    trigger: 'Schedule - Weekly',
    actions: ['Google Sheets - Update Row', 'Slack - Send Message'],
    status: 'active',
    executions: 8,
    successRate: 87.5,
    lastExecuted: '2 days ago',
    created: '2024-01-05',
    priority: 'medium'
  },
  {
    id: 4,
    name: 'Customer Feedback Collection',
    description: 'Collect feedback after ticket resolution',
    trigger: 'Zendesk - Ticket Solved',
    actions: ['Trello - Add Comment'],
    status: 'paused',
    executions: 156,
    successRate: 94.2,
    lastExecuted: '1 week ago',
    created: '2023-12-20',
    priority: 'low'
  },
  {
    id: 5,
    name: 'Bug Report Tracking',
    description: 'Track bug reports in development board',
    trigger: 'Jira - Issue Created',
    actions: ['Slack - Send Message', 'Notion - Create Database Entry'],
    status: 'error',
    executions: 12,
    successRate: 75.0,
    lastExecuted: '3 hours ago',
    created: '2024-01-20',
    priority: 'high'
  }
];

const getStatusColor = (status) => {
  switch (status) {
    case 'active':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
    case 'paused':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'active':
      return <CheckCircle className="h-4 w-4" />;
    case 'paused':
      return <Pause className="h-4 w-4" />;
    case 'error':
      return <XCircle className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
};

const getPriorityColor = (priority) => {
  switch (priority) {
    case 'critical':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'medium':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    case 'low':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
  }
};

const RuleRow = ({ rule, onEdit, onDelete, onToggleStatus, onDuplicate, onTest }) => (
  <TableRow className="hover:bg-gray-50 dark:hover:bg-gray-800">
    <TableCell>
      <div className="flex items-start space-x-3">
        <div className={`p-2 rounded-lg ${getStatusColor(rule.status)}`}>
          {getStatusIcon(rule.status)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {rule.name}
            </p>
            <Badge variant="secondary" className={getPriorityColor(rule.priority)}>
              {rule.priority}
            </Badge>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {rule.description}
          </p>
          <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
            <span>Trigger: {rule.trigger}</span>
            <span>•</span>
            <span>{rule.actions.length} action(s)</span>
          </div>
        </div>
      </div>
    </TableCell>
    <TableCell>
      <Badge variant="outline" className={getStatusColor(rule.status)}>
        {rule.status}
      </Badge>
    </TableCell>
    <TableCell className="text-center">
      <div className="text-sm font-medium text-gray-900 dark:text-white">
        {rule.executions}
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        executions
      </div>
    </TableCell>
    <TableCell className="text-center">
      <div className="text-sm font-medium text-gray-900 dark:text-white">
        {rule.successRate}%
      </div>
      <div className="text-xs text-gray-500 dark:text-gray-400">
        success rate
      </div>
    </TableCell>
    <TableCell className="text-sm text-gray-500 dark:text-gray-400">
      {rule.lastExecuted}
    </TableCell>
    <TableCell>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>Actions</DropdownMenuLabel>
          <DropdownMenuItem onClick={() => onTest(rule)}>
            <Play className="mr-2 h-4 w-4" />
            Test Rule
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onToggleStatus(rule)}>
            {rule.status === 'active' ? (
              <>
                <Pause className="mr-2 h-4 w-4" />
                Pause Rule
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Activate Rule
              </>
            )}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => onEdit(rule)}>
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onDuplicate(rule)}>
            <Copy className="mr-2 h-4 w-4" />
            Duplicate
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem 
            onClick={() => onDelete(rule)}
            className="text-red-600 dark:text-red-400"
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </TableCell>
  </TableRow>
);

export const RulesPage = () => {
  const [rules, setRules] = useState(mockRules);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const filteredRules = rules.filter(rule => {
    const matchesSearch = rule.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         rule.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || rule.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleEdit = (rule) => {
    console.log('Edit rule:', rule);
    // TODO: Open edit dialog
  };

  const handleDelete = (rule) => {
    console.log('Delete rule:', rule);
    // TODO: Show confirmation dialog and delete
  };

  const handleToggleStatus = (rule) => {
    const newStatus = rule.status === 'active' ? 'paused' : 'active';
    setRules(rules.map(r => 
      r.id === rule.id ? { ...r, status: newStatus } : r
    ));
  };

  const handleDuplicate = (rule) => {
    const newRule = {
      ...rule,
      id: Math.max(...rules.map(r => r.id)) + 1,
      name: `${rule.name} (Copy)`,
      status: 'paused',
      executions: 0,
      successRate: 0,
      lastExecuted: 'Never',
      created: new Date().toISOString().split('T')[0]
    };
    setRules([...rules, newRule]);
  };

  const handleTest = (rule) => {
    console.log('Test rule:', rule);
    // TODO: Execute test run
  };

  const getStatusCounts = () => {
    return {
      all: rules.length,
      active: rules.filter(r => r.status === 'active').length,
      paused: rules.filter(r => r.status === 'paused').length,
      error: rules.filter(r => r.status === 'error').length
    };
  };

  const statusCounts = getStatusCounts();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Automation Rules
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Create and manage your automation workflows
          </p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              <Plus className="h-4 w-4 mr-2" />
              Create Rule
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New Rule</DialogTitle>
              <DialogDescription>
                Set up a new automation rule to streamline your workflows.
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <p className="text-sm text-gray-500">
                Rule creation form would go here...
              </p>
            </div>
          </DialogContent>
        </Dialog>
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
                <Zap className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {statusCounts.all}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Total Rules
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
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {statusCounts.active}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Active Rules
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
                <Pause className="h-5 w-5 text-yellow-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {statusCounts.paused}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Paused Rules
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
                <AlertTriangle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {statusCounts.error}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Error Rules
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Filters and Search */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Rules Management</CardTitle>
              <CardDescription>
                Manage your automation rules and monitor their performance
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex-1 max-w-sm">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search rules..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline">
                  <Filter className="h-4 w-4 mr-2" />
                  Status: {statusFilter === 'all' ? 'All' : statusFilter}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setStatusFilter('all')}>
                  All ({statusCounts.all})
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setStatusFilter('active')}>
                  Active ({statusCounts.active})
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setStatusFilter('paused')}>
                  Paused ({statusCounts.paused})
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setStatusFilter('error')}>
                  Error ({statusCounts.error})
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          {/* Rules Table */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Rule</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-center">Executions</TableHead>
                  <TableHead className="text-center">Success Rate</TableHead>
                  <TableHead>Last Executed</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRules.length > 0 ? (
                  filteredRules.map((rule) => (
                    <RuleRow
                      key={rule.id}
                      rule={rule}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onToggleStatus={handleToggleStatus}
                      onDuplicate={handleDuplicate}
                      onTest={handleTest}
                    />
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="flex flex-col items-center space-y-2">
                        <Zap className="h-8 w-8 text-gray-400" />
                        <p className="text-gray-500 dark:text-gray-400">
                          {searchTerm || statusFilter !== 'all' 
                            ? 'No rules match your filters' 
                            : 'No rules created yet'
                          }
                        </p>
                        {!searchTerm && statusFilter === 'all' && (
                          <Button 
                            onClick={() => setIsCreateDialogOpen(true)}
                            variant="outline"
                            size="sm"
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            Create Your First Rule
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

