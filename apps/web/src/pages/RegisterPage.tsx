import { FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card, Input, Space, Typography } from '@douyinfe/semi-ui';

import { useAuth } from '../contexts/AuthContext';
import { registerUser } from '../services/api';
import { ApiError } from '../services/http';

function validatePassword(value: string): string | null {
  if (value.length < 8) {
    return '密码至少 8 位';
  }
  if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) {
    return '密码需同时包含字母和数字';
  }
  return null;
}

export function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage('');

    const passwordError = validatePassword(password);
    if (passwordError) {
      setErrorMessage(passwordError);
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('两次密码输入不一致');
      return;
    }

    setSubmitting(true);
    try {
      await registerUser(email.trim(), password);
      await login(email.trim(), password);
      navigate('/app/profile/setup', { replace: true });
    } catch (error) {
      if (error instanceof ApiError) {
        setErrorMessage(error.message);
      } else {
        setErrorMessage('注册失败，请稍后重试。');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <Card className="auth-card" shadows="always">
        <Typography.Title heading={3} style={{ marginBottom: 4 }}>
          注册账号
        </Typography.Title>
        <Typography.Text type="tertiary">注册成功后将自动登录，并进入首次资料维护页面。</Typography.Text>

        <form onSubmit={handleSubmit} className="auth-form">
          <Space vertical align="start" style={{ width: '100%' }}>
            <label className="form-label" htmlFor="register-email">
              邮箱
            </label>
            <Input
              id="register-email"
              value={email}
              onChange={setEmail}
              placeholder="user@example.com"
              size="large"
            />

            <label className="form-label" htmlFor="register-password">
              密码
            </label>
            <Input
              id="register-password"
              mode="password"
              value={password}
              onChange={setPassword}
              placeholder="至少 8 位，需包含字母和数字"
              size="large"
            />

            <label className="form-label" htmlFor="register-password-confirm">
              确认密码
            </label>
            <Input
              id="register-password-confirm"
              mode="password"
              value={confirmPassword}
              onChange={setConfirmPassword}
              placeholder="再次输入密码"
              size="large"
            />

            {errorMessage ? <Typography.Text type="danger">{errorMessage}</Typography.Text> : null}

            <Button htmlType="submit" theme="solid" size="large" loading={submitting} style={{ width: '100%' }}>
              注册并登录
            </Button>
          </Space>
        </form>

        <Typography.Text type="tertiary">
          已有账号？<Link to="/auth/login">去登录</Link>
        </Typography.Text>
      </Card>
    </div>
  );
}
