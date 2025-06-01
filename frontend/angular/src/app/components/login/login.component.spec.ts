import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { LoginComponent } from './login.component';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import { By } from '@angular/platform-browser';
import { environment } from '../../../environments/environment';

describe('LoginComponent', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let apiService: ApiService;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    const routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [
        ReactiveFormsModule,
        HttpClientTestingModule,
        LoginComponent // Como es un componente standalone
      ],
      providers: [
        ApiService,
        { provide: Router, useValue: routerSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    // Espiar el EventEmitter closeModal
    spyOn(component.closeModal, 'emit');
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify(); // Verifica que no haya peticiones HTTP pendientes
  });

  it('debería crear el componente', () => {
    expect(component).toBeTruthy();
  });

  it('debería tener un formulario inválido si los campos están vacíos', () => {
    expect(component.loginForm.valid).toBeFalse();
    expect(component.loginForm.get('email')?.errors?.['required']).toBeTruthy();
    expect(component.loginForm.get('password')?.errors?.['required']).toBeTruthy();
  });

  it('debería tener un formulario válido con datos correctos', () => {
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'password123'
    });
    expect(component.loginForm.valid).toBeTrue();
  });

  it('debería mostrar un error si el correo tiene un formato inválido', () => {
    component.loginForm.setValue({
      email: 'invalid-email',
      password: 'password123'
    });
    expect(component.loginForm.get('email')?.errors?.['email']).toBeTruthy();
    expect(component.loginForm.valid).toBeFalse();

    // Forzar la detección de cambios para renderizar el mensaje de error
    component.loginForm.get('email')?.markAsTouched();
    fixture.detectChanges();

    const errorElement = fixture.debugElement.query(By.css('.text-red-500'));
    if (errorElement) {
      expect(errorElement.nativeElement.textContent).toContain('Formato de correo inválido');
    } else {
      fail('No se encontró el elemento de error con la clase .text-red-500');
    }
  });

  it('debería llamar al ApiService y navegar a /principal en un login exitoso', async () => {
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'password123'
    });

    component.submitLogin();

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ correo: 'test@example.com', contrasena: 'password123' });

    req.flush({
      token: 'mocked_token',
      rol: 'usuario',
      nombre: 'Test User'
    });

    await fixture.whenStable();
    expect(localStorage.getItem('token')).toBe('mocked_token');
    expect(localStorage.getItem('rol')).toBe('usuario');
    expect(localStorage.getItem('correo')).toBe('test@example.com');
    expect(localStorage.getItem('nombre')).toBe('Test User');
    expect(component.closeModal.emit).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(['/principal']);
  });

  it('debería mostrar un mensaje de error en un login fallido', async () => {
    component.loginForm.setValue({
      email: 'test@example.com',
      password: 'wrongpassword'
    });

    component.submitLogin();

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    req.flush({ detail: 'Credenciales incorrectas' }, { status: 401, statusText: 'Unauthorized' });

    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.error).toBe('Error al iniciar sesión: Credenciales incorrectas');
    const errorElement = fixture.debugElement.query(By.css('.text-red-500'));
    if (errorElement) {
      expect(errorElement.nativeElement.textContent).toContain('Credenciales incorrectas');
    } else {
      fail('No se encontró el elemento de error con la clase .text-red-500');
    }
  });

  it('debería alternar la visibilidad de la contraseña', () => {
    const input = fixture.debugElement.query(By.css('#password')).nativeElement;
    expect(input.type).toBe('password');

    component.togglePasswordVisibility();
    fixture.detectChanges();
    expect(input.type).toBe('text');

    component.togglePasswordVisibility();
    fixture.detectChanges();
    expect(input.type).toBe('password');
  });
});