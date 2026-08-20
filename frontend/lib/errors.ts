export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public message: string,
    public isRetryable: boolean = true,
    public requestId?: string,
    public endpoint?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface FormattedError {
  title: string
  message: string
  requestId?: string
  endpoint?: string
  statusCode?: number
  isRetryable: boolean
}

export function formatError(error: unknown, fallbackMessage = 'An unexpected error occurred'): FormattedError {
  if (error instanceof ApiError) {
    let title = 'Request Failed'
    if (error.status === 404) title = 'Resource Not Found'
    else if (error.status === 429) title = 'Rate Limit Exceeded'
    else if (error.status === 401 || error.status === 403) title = 'Authentication Error'
    else if (error.status >= 500) title = 'Server Error'
    else if (error.status === 0) title = 'Network Disconnected'

    return {
      title,
      message: error.message || fallbackMessage,
      requestId: error.requestId,
      endpoint: error.endpoint,
      statusCode: error.status,
      isRetryable: error.isRetryable,
    }
  }

  if (error instanceof Error) {
    return {
      title: 'Application Error',
      message: error.message || fallbackMessage,
      isRetryable: true,
    }
  }

  return {
    title: 'Unknown Error',
    message: typeof error === 'string' ? error : fallbackMessage,
    isRetryable: true,
  }
}
