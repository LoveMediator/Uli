import { http, HttpResponse } from 'msw';

export const handlers = [
  http.post('/api/v1/auth/login', () =>
    HttpResponse.json({
      code: 0,
      message: 'ok',
      data: {
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        tokenType: 'bearer',
        userId: 1,
        publicId: 'u_test',
      },
    })),
];
