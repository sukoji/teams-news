import { Component, type ErrorInfo, type ReactNode } from "react";
import { Link } from "react-router-dom";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("App error:", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="ss-card mx-auto max-w-lg p-8 text-center">
          <h1 className="mb-2 text-lg font-semibold text-text-primary">문제가 발생했습니다</h1>
          <p className="mb-4 text-sm text-text-tertiary">
            페이지를 불러오는 중 오류가 발생했습니다. 네트워크 연결을 확인하거나 잠시 후 다시
            시도해 주세요.
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            <button
              type="button"
              className="ss-chip ss-chip-active touch-target"
              onClick={() => window.location.reload()}
            >
              새로고침
            </button>
            <Link to="/" className="ss-chip touch-target no-underline">
              홈으로
            </Link>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
