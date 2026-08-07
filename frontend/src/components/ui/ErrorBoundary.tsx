import { Component } from "react"

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface State {
  hasError: boolean
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex items-center justify-center min-h-40 p-6">
            <div className="text-center">
              <p className="text-lg text-text mb-2">Something went wrong</p>
              <button
                onClick={() => this.setState({ hasError: false })}
                className="text-sm text-accent hover:text-accent-hover transition-colors"
              >
                Try again
              </button>
            </div>
          </div>
        )
      )
    }
    return this.props.children
  }
}
