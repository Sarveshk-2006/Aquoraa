export interface LivenessResponse {
  status: string;
}

export interface ServicesHealth {
  database: string;
  redis: string;
}

export interface ReadinessResponse {
  status: string;
  environment?: string;
  services: ServicesHealth;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
