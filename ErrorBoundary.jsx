import { Component } from 'react';

export default class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, info: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, info) {
        console.error('React Error Boundary caught:', error, info);
        this.setState({ info });
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: 40, color: '#EF4444', background: '#1E293B', minHeight: '100vh', fontFamily: 'Inter, sans-serif' }}>
                    <h2>⚠️ Something went wrong</h2>
                    <pre style={{ color: '#F59E0B', fontSize: 13, whiteSpace: 'pre-wrap', marginTop: 16 }}>
                        {this.state.error?.toString()}
                    </pre>
                    <pre style={{ color: '#94A3B8', fontSize: 11, whiteSpace: 'pre-wrap', marginTop: 12 }}>
                        {this.state.info?.componentStack}
                    </pre>
                    <button onClick={() => this.setState({ hasError: false, error: null, info: null })}
                        style={{ marginTop: 20, padding: '8px 20px', background: '#3B82F6', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                        Try Again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}
