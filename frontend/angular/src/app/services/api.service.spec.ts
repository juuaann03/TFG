import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify(); // Verifica que no haya peticiones HTTP pendientes
  });

  it('debería ser creado', () => {
    expect(service).toBeTruthy();
  });

  it('debería realizar una petición GET con cabeceras correctas', () => {
    localStorage.setItem('token', 'test-token');

    service.get<{ data: string }>('test/endpoint').subscribe(response => {
      expect(response).toEqual({ data: 'test' });
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/test/endpoint`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    expect(req.request.headers.get('Content-Type')).toBe('application/json');
    req.flush({ data: 'test' });
  });

  it('debería realizar una petición POST con cuerpo y cabeceras correctas', () => {
    localStorage.setItem('token', 'test-token');

    const body = { correo: 'test@example.com', contrasena: 'password123' };
    service.post<{ token: string }>('auth/login', body).subscribe(response => {
      expect(response).toEqual({ token: 'mocked_token' });
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(body);
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    expect(req.request.headers.get('Content-Type')).toBe('application/json');
    req.flush({ token: 'mocked_token' });
  });

  it('debería realizar una petición PUT con cuerpo vacío si no se proporciona', () => {
    service.put<{ message: string }>('test/endpoint').subscribe(response => {
      expect(response).toEqual({ message: 'updated' });
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/test/endpoint`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual({});
    req.flush({ message: 'updated' });
  });

  it('debería realizar una petición DELETE', () => {
    service.delete<{ message: string }>('test/endpoint').subscribe(response => {
      expect(response).toEqual({ message: 'deleted' });
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/test/endpoint`);
    expect(req.request.method).toBe('DELETE');
    req.flush({ message: 'deleted' });
  });
});