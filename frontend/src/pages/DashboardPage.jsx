import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { 
  Activity, 
  Zap, 
  Users, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Puzzle,
  Shield,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw
} from 'lucide-react';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Mock data - replace with real API calls
const mockStats = {
  totalRules: 24,
  activeRules: 18,
  totalExecutions: 1247,
  successRate: 94.2,
  avgResponseTime: 1.8,
  integrations: 6,
  activeUsers: 12,
  recentAlerts: 3
};

const mockExecutionData = [
  { name: 'Mon', executions: 45, success: 42, failed: 3 },
  { name: 'Tue', executions: 52, success: 49, failed: 3 },
  { name: 'Wed', executions: 38, success: 36, failed: 2 },
  { name: 'Thu', executions: 61, success: 58, failed: 3 },
  { name: 'Fri', executions: 55, success: 52, failed: 3 },
  { name: 'Sat', executions: 28, success: 27, failed: 1 },
  { name: 'Sun', executions: 32, success: 31, failed: 1 }
];

const mockIntegrationData = [
  { name: 'Slack', value: 35, color: '#4A154B' },
  { name: 'Trello', value: 25, color: '#0079BF' },
  { name: 'Notion', value: 20, color: '#000000' },
  { name: 'Google Sheets', value: 15, color: '#34A853' },
  { name: 'Others', value: 5, color: '#9CA3AF' }
];

const mockRecentActivity = [
  {
    id: 1,
    type: 'rule_executed',
    title: 'Ticket Auto-Assignment Rule',
    description: 'Successfully assigned ticket #1234 to John Doe',
    timestamp: '2 minutes ago',
    status: 'success'
  },
  {
    id: 2,
    type: 'integration_connected',
    title: 'Slack Integration',
    description: 'New Slack workspace connected',
    timestamp: '15 minutes ago',
    status: 'info'
  },
  {
    id: 3,
    type: 'rule_failed',
    title: 'Notification Rule',
    description: 'Failed to send notification - API rate limit exceeded',
    timestamp: '1 hour ago',
    status: 'error'
  },
  {
    id: 4,
    type: 'user_login',
    title: 'User Login',
    description: 'Sarah Johnson logged in from new device',
    timestamp: '2 hours ago',
    status: 'info'
  }
];

const StatCard = ({ title, value, change, changeType, icon: Icon, description }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.3 }}
  >
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-gray-400" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </div>
        {change && (
          <div className="flex items-center space-x-1 mt-1">
            {changeType === 'increase' ? (
              <ArrowUpRight className="h-3 w-3 text-green-500" />
            ) : (
              <ArrowDownRight className="h-3 w-3 text-red-500" />
            )}
            <span className={`text-xs ${changeType === 'increase' ? 'text-green-600' : 'text-red-600'}`}>
              {change}
            </span>
            <span className="text-xs text-gray-500">from last week</span>
          </div>
        )}
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  </motion.div>
);

const ActivityItem = ({ activity }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'info':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  const getStatusIcon = (type) => {
    switch (type) {
      case 'rule_executed':
        return <Zap className="h-4 w-4" />;
      case 'integration_connected':
        return <Puzzle className="h-4 w-4" />;
      case 'rule_failed':
        return <AlertTriangle className="h-4 w-4" />;
      case 'user_login':
        return <Users className="h-4 w-4" />;
      default:
        return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="flex items-start space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors">
      <div className={`p-2 rounded-full ${getStatusColor(activity.status)}`}>
        {getStatusIcon(activity.type)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white">
          {activity.title}
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {activity.description}
        </p>
        <p className="text-xs text-gray-400 mt-1">
          {activity.timestamp}
        </p>
      </div>
    </div>
  );
};

export const DashboardPage = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [refreshTime, setRefreshTime] = useState(new Date());

  const handleRefresh = async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshTime(new Date());
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor your automation performance and system health
          </p>
        </div>
        <Button 
          onClick={handleRefresh} 
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Active Rules"
          value={mockStats.activeRules}
          change="+12%"
          changeType="increase"
          icon={Zap}
          description={`${mockStats.totalRules} total rules`}
        />
        <StatCard
          title="Success Rate"
          value={`${mockStats.successRate}%`}
          change="+2.1%"
          changeType="increase"
          icon={CheckCircle}
          description="Last 7 days"
        />
        <StatCard
          title="Total Executions"
          value={mockStats.totalExecutions.toLocaleString()}
          change="+18%"
          changeType="increase"
          icon={Activity}
          description="This month"
        />
        <StatCard
          title="Avg Response Time"
          value={`${mockStats.avgResponseTime}s`}
          change="-0.3s"
          changeType="increase"
          icon={Clock}
          description="System performance"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Execution Trends */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BarChart3 className="h-5 w-5" />
                <span>Execution Trends</span>
              </CardTitle>
              <CardDescription>
                Daily rule executions over the past week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={mockExecutionData}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="success" 
                    stackId="1"
                    stroke="#10b981" 
                    fill="#10b981" 
                    fillOpacity={0.6}
                    name="Successful"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="failed" 
                    stackId="1"
                    stroke="#ef4444" 
                    fill="#ef4444" 
                    fillOpacity={0.6}
                    name="Failed"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Integration Usage */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Puzzle className="h-5 w-5" />
                <span>Integration Usage</span>
              </CardTitle>
              <CardDescription>
                Distribution of rule executions by platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={mockIntegrationData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {mockIntegrationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value) => [`${value}%`, 'Usage']}
                    contentStyle={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-2 mt-4">
                {mockIntegrationData.map((item, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {item.name}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {item.value}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Activity className="h-5 w-5" />
                <span>Recent Activity</span>
              </CardTitle>
              <CardDescription>
                Latest system events and rule executions
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {mockRecentActivity.map((activity) => (
                  <ActivityItem key={activity.id} activity={activity} />
                ))}
              </div>
              <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                <Button variant="ghost" size="sm" className="w-full">
                  View All Activity
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* System Health */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5" />
                <span>System Health</span>
              </CardTitle>
              <CardDescription>
                Current system status and metrics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    API Response Time
                  </span>
                  <span className="text-sm font-medium text-green-600">
                    Excellent
                  </span>
                </div>
                <Progress value={92} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Database Performance
                  </span>
                  <span className="text-sm font-medium text-green-600">
                    Good
                  </span>
                </div>
                <Progress value={85} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Integration Health
                  </span>
                  <span className="text-sm font-medium text-yellow-600">
                    Warning
                  </span>
                </div>
                <Progress value={78} className="h-2" />
              </div>

              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">
                    Last updated
                  </span>
                  <span className="text-gray-900 dark:text-white">
                    {refreshTime.toLocaleTimeString()}
                  </span>
                </div>
              </div>

              <Button variant="outline" size="sm" className="w-full">
                View Detailed Metrics
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

