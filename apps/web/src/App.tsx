import { Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { Card, Empty, Spin } from '@douyinfe/semi-ui';

import { AppFrame } from './components/AppFrame';
import { useAuth } from './contexts/AuthContext';
import { ComingSoonPage } from './pages/ComingSoonPage';
import { HealthConnectorConfigPage } from './pages/HealthConnectorConfigPage';
import { HealthDomainPage } from './pages/HealthDomainPage';
import { HealthMartPage } from './pages/HealthMartPage';
import { LoginPage } from './pages/LoginPage';
import { ProfileSetupPage } from './pages/ProfileSetupPage';
import { RegisterPage } from './pages/RegisterPage';
import { SystemSourcesPage } from './pages/SystemSourcesPage';

function RouteLoading() {
  return (
    <div className="route-loading">
      <Card>
        <Spin spinning tip="正在恢复会话...">
          <Empty title="加载中" description="正在校验登录状态" />
        </Spin>
      </Card>
    </div>
  );
}

function RequireAuth() {
  const { bootstrapping, user } = useAuth();
  if (bootstrapping) {
    return <RouteLoading />;
  }
  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }
  return <Outlet />;
}

function RequireProfileCompleted() {
  const { user } = useAuth();
  if (!user?.profile_completed) {
    return <Navigate to="/app/profile/setup" replace />;
  }
  return <Outlet />;
}

function RequirePermission({ permissionCode }: { permissionCode: string }) {
  const { hasPermission } = useAuth();
  if (!hasPermission(permissionCode)) {
    return (
      <Card title="权限不足" shadows="hover">
        <Empty title="403" description={`当前账号缺少权限：${permissionCode}`} />
      </Card>
    );
  }
  return <Outlet />;
}

function HomeRedirect() {
  const { bootstrapping, user } = useAuth();

  if (bootstrapping) {
    return <RouteLoading />;
  }
  if (!user) {
    return <Navigate to="/auth/login" replace />;
  }
  if (!user.profile_completed) {
    return <Navigate to="/app/profile/setup" replace />;
  }
  return <Navigate to="/app/health/overview" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/auth/login" element={<LoginPage />} />
      <Route path="/auth/register" element={<RegisterPage />} />

      <Route element={<RequireAuth />}>
        <Route path="/app/profile/setup" element={<ProfileSetupPage />} />

        <Route element={<RequireProfileCompleted />}>
          <Route path="/app" element={<AppFrame />}>
            <Route index element={<Navigate to="/app/health/overview" replace />} />
            <Route element={<RequirePermission permissionCode="health.mart.read" />}>
              <Route path="health/connectors" element={<HealthConnectorConfigPage />} />
            </Route>

            <Route element={<RequirePermission permissionCode="health.domain.read" />}>
              <Route path="health/domain" element={<HealthDomainPage />} />
            </Route>

            <Route element={<RequirePermission permissionCode="health.mart.read" />}>
              <Route path="health/overview" element={<HealthMartPage />} />
              <Route path="health/mart" element={<HealthMartPage />} />
            </Route>

            <Route path="system-sources" element={<SystemSourcesPage />} />

            <Route path="time" element={<ComingSoonPage title="时间模块" />} />
            <Route path="income" element={<ComingSoonPage title="收入模块" />} />
            <Route path="finance" element={<ComingSoonPage title="财务模块" />} />
            <Route path="ability" element={<ComingSoonPage title="能力模块" />} />
            <Route path="relationship" element={<ComingSoonPage title="关系模块" />} />
            <Route path="life" element={<ComingSoonPage title="生活模块" />} />
            <Route path="security" element={<ComingSoonPage title="保障模块" />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
