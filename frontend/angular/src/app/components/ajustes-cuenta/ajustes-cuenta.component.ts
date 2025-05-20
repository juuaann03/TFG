import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router, RouterModule } from '@angular/router';
import { UsuarioOpcionalSinHistorial } from '../../models/usuario-opcional-sin-historial';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-ajustes-cuenta',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule],
  templateUrl: './ajustes-cuenta.component.html',
  styleUrls: ['./ajustes-cuenta.component.scss']
})
export class AjustesCuentaComponent implements OnInit, OnDestroy {
  datosForm: FormGroup; // Para modificar nombre/contraseña
  peticionForm: FormGroup; // Para modificar datos opcionales por petición
  steamForm: FormGroup; // Nuevo formulario para SteamID
  datosOpcionales: UsuarioOpcionalSinHistorial | null = null;
  nombreUsuario: string | null = null;
  error: string | null = null;
  isLoading = false; // Para operaciones generales
  isLoadingPeticion = false; // Para la petición de modificar datos
  isLoadingSteam = false; // Para la conexión con Steam
  isDarkMode = false;
  showModal = false; // Para el modal de modificar datos
  showSteamModal = false; // Para el modal de Steam
  showCurrentPassword = false; // Para controlar visibilidad de contraseña actual
  showNewPassword = false; // Para controlar visibilidad de nueva contraseña
  private destroy$ = new Subject<void>();
  introText: string = ''; // Texto de introducción para personalizar preferencias
  placeholderText: string = ''; // Placeholder para el textarea de preferencias

  private introTexts: string[] = [
    'Cuéntanos qué juegos te gustan, cuáles no, o las consolas que tienes. También puedes mencionar necesidades especiales, como subtítulos grandes, para personalizar tus recomendaciones.',
    'Dinos qué juegos has jugado, tu configuración de PC, o si necesitas controles adaptados por problemas psicomotrices. ¡Haremos que tus recomendaciones sean perfectas!',
    'Comparte tus juegos favoritos, los que no te gustan, o los idiomas que prefieres. Si tienes consolas específicas o necesidades de accesibilidad, menciónalas aquí.',
    'Indica qué juegos posees, en qué plataformas, o si hablas ciertos idiomas. También puedes mencionar problemas como de visión para recomendaciones más personalizadas a tu condiciones.',
    'Ayúdanos a conocerte mejor: ¿qué juegos te encantan o has jugado? ¿Qué consolas usas? ¿Tienes necesidades especiales, como controles simplificados?'
  ];

  private placeholderTexts: string[] = [
    'Ejemplo: Me gusta mucho The Witcher 3, tengo una PS5 y un PC con RTX 3070, hablo español e inglés, necesito subtítulos grandes.',
    'Ejemplo: No me gusta Call of Duty Black Ops 5, tengo una Xbox Series X, he jugado Zelda en Switch, necesito controles adaptados por problemas psicomotrices.',
    'Ejemplo: Poseo una Nintendo Switch con Mario Odyssey, me gusta mucho Zelda Breath of the Wild, hablo francés, tengo problemas de visión.',
    'Ejemplo: Tengo un PC con 16GB RAM y GTX 1660, no me gusta Residente Evil 6, tengo Skyrim en pc, prefiero juegos en español.',
    'Ejemplo: Juego en PS4, tengo God of War y me gusta mucho, hablo inglés, necesito opciones de accesibilidad para daltonismo.'
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    // Formulario para modificar datos obligatorios
    this.datosForm = this.fb.group({
      currentPassword: ['', Validators.required],
      newName: [''],
      newPassword: ['', [
        Validators.minLength(8),
        Validators.pattern(/^(?=.*[A-Za-z])(?=.*\d)/)
      ]]
    });

    // Formulario para la petición de datos opcionales
    this.peticionForm = this.fb.group({
      peticion: ['', Validators.required]
    });

    // Formulario para el SteamID
    this.steamForm = this.fb.group({
      steamId: ['', [Validators.required, Validators.pattern(/^\d{17}$/)]]
    });
  }

  ngOnInit(): void {
    // Cargar tema desde localStorage
    this.isDarkMode = localStorage.getItem('theme') === 'dark';
    document.documentElement.classList.toggle('dark', this.isDarkMode);

    // Obtener nombre del usuario desde localStorage
    this.nombreUsuario = localStorage.getItem('nombre') || null;

    // Cargar datos opcionales
    this.cargarDatosOpcionales();

    // Seleccionar texto de introducción y placeholder aleatorios
    this.introText = this.introTexts[Math.floor(Math.random() * this.introTexts.length)];
    this.placeholderText = this.placeholderTexts[Math.floor(Math.random() * this.placeholderTexts.length)];
  }

  toggleTheme(): void {
    this.isDarkMode = !this.isDarkMode;
    document.documentElement.classList.toggle('dark', this.isDarkMode);
    localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
  }

  toggleCurrentPasswordVisibility(): void {
    this.showCurrentPassword = !this.showCurrentPassword;
  }

  toggleNewPasswordVisibility(): void {
    this.showNewPassword = !this.showNewPassword;
  }

  cargarDatosOpcionales(): void {
    const correo = localStorage.getItem('correo') || '';
    if (!correo) {
      this.error = 'No se encontró el correo del usuario';
      return;
    }

    this.isLoading = true;
    this.apiService.get<UsuarioOpcionalSinHistorial>(`usuarios/porCorreo/${correo}/optativos`).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response: UsuarioOpcionalSinHistorial) => {
        this.datosOpcionales = response;
        this.isLoading = false;
      },
      error: (err: any) => {
        this.error = 'Error al cargar datos opcionales: ' + (err.error?.detail || err.message);
        this.isLoading = false;
      }
    });
  }

  openModal(): void {
    this.showModal = true;
    this.datosForm.reset();
    this.error = null;
  }

  closeModal(): void {
    this.showModal = false;
    this.datosForm.reset();
    this.error = null;
  }

  openSteamModal(): void {
    this.showSteamModal = true;
    this.steamForm.reset();
    this.error = null;
  }

  closeSteamModal(): void {
    this.showSteamModal = false;
    this.steamForm.reset();
    this.error = null;
  }

  submitDatos(): void {
    if (this.datosForm.valid) {
      const { currentPassword, newName, newPassword } = this.datosForm.value;
      const correo = localStorage.getItem('correo') || '';
      if (!correo) {
        this.error = 'No se encontró el correo del usuario';
        return;
      }

      // Verificar contraseña actual
      this.isLoading = true;
      this.apiService.post<any>('auth/login', { correo, contrasena: currentPassword }).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: () => {
          // Contraseña correcta, proceder con la actualización
          const datosActualizados: any = {};
          if (newName) datosActualizados.nombre = newName;
          if (newPassword) datosActualizados.contrasena = newPassword;

          if (Object.keys(datosActualizados).length === 0) {
            this.error = 'No se proporcionaron datos para actualizar';
            this.isLoading = false;
            return;
          }

          // Confirmar cambios
          if (!window.confirm('¿Estás seguro de que quieres modificar los datos de tu cuenta?')) {
            this.isLoading = false;
            return;
          }

          this.apiService.put<any>(`usuarios/porCorreo/${correo}/obligatorios`, datosActualizados).pipe(
            takeUntil(this.destroy$)
          ).subscribe({
            next: (response: { mensaje: string }) => {
              if (newName) {
                localStorage.setItem('nombre', newName);
                this.nombreUsuario = newName;
              }
              this.closeModal();
              this.isLoading = false;
              alert(response.mensaje);
            },
            error: (err: any) => {
              let errorMessage = 'Error al actualizar datos';
              if (err.error?.detail) {
                errorMessage += `: ${err.error.detail}`;
              } else if (err.status === 405) {
                errorMessage += ': Método no permitido. Contacta al administrador.';
              } else {
                errorMessage += `: ${err.message || 'Error desconocido'}`;
              }
              this.error = errorMessage;
              this.isLoading = false;
            }
          });
        },
        error: (err: any) => {
          this.error = 'Contraseña actual incorrecta';
          this.isLoading = false;
        }
      });
    }
  }

  submitSteam(): void {
    if (this.steamForm.valid) {
      this.isLoadingSteam = true;
      this.error = null;
      const correo = localStorage.getItem('correo') || '';
      if (!correo) {
        this.error = 'No se encontró el correo del usuario';
        this.isLoadingSteam = false;
        return;
      }

      const steamId = this.steamForm.value.steamId;
      this.apiService.post<any>(`usuarios/porCorreo/${correo}/steam`, { steam_id: steamId }).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (response: { mensaje: string; juegos_anadidos: number; juegos_jugados_anadidos: number }) => {
          this.steamForm.reset();
          this.closeSteamModal();
          this.cargarDatosOpcionales(); // Recargar datos opcionales para mostrar los nuevos juegos
          this.isLoadingSteam = false;
          alert(`${response.mensaje}. Juegos añadidos: ${response.juegos_anadidos}, Juegos jugados añadidos: ${response.juegos_jugados_anadidos}`);
        },
        error: (err: any) => {
          this.error = 'Error al conectar con Steam: ' + (err.error?.detail || err.message);
          this.isLoadingSteam = false;
        }
      });
    }
  }

  deleteAccount(): void {
    const correo = localStorage.getItem('correo') || '';
    if (!correo) {
      this.error = 'No se encontró el correo del usuario';
      return;
    }

    if (!window.confirm('¿Estás seguro de que quieres eliminar tu cuenta? Esta acción no se puede deshacer.')) {
      return;
    }

    this.isLoading = true;
    this.apiService.delete<any>(`usuarios/porCorreo/${correo}`).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        localStorage.clear();
        this.isLoading = false;
        alert('Cuenta eliminada correctamente');
        this.router.navigate(['/']);
      },
      error: (err: any) => {
        this.error = 'Error al eliminar cuenta: ' + (err.error?.detail || err.message);
        this.isLoading = false;
      }
    });
  }

  resetDatosVideojuegos(): void {
    const correo = localStorage.getItem('correo') || '';
    if (!correo) {
      this.error = 'No se encontró el correo del usuario';
      return;
    }

    if (!window.confirm('¿Estás seguro de que quieres restablecer tus datos sobre videojuegos? Esto eliminará consolas, preferencias y más.')) {
      return;
    }

    this.isLoading = true;
    this.apiService.put<any>(`usuarios/porCorreo/${correo}/limpiar`, {}).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: () => {
        this.cargarDatosOpcionales();
        this.isLoading = false;
        alert('Datos sobre videojuegos restablecidos correctamente');
      },
      error: (err: any) => {
        this.error = 'Error al restablecer datos: ' + (err.error?.detail || err.message);
        this.isLoading = false;
      }
    });
  }

  submitPeticion(): void {
    if (this.peticionForm.valid) {
      this.isLoadingPeticion = true;
      this.error = null;
      const correo = localStorage.getItem('correo') || '';
      if (!correo) {
        this.error = 'No se encontró el correo del usuario';
        this.isLoadingPeticion = false;
        return;
      }

      const peticion = this.peticionForm.value.peticion;
      this.apiService.put<any>(`usuarios/porCorreo/${correo}/modificarPorPeticion`, { peticion }).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (response: { mensaje: string; actualizacion: any }) => {
          this.peticionForm.reset();
          this.cargarDatosOpcionales();
          this.isLoadingPeticion = false;
          alert(response.mensaje);
        },
        error: (err: any) => {
          this.error = 'Error al procesar la petición: ' + (err.error?.detail || err.message || 'Error desconocido');
          this.isLoadingPeticion = false;
        }
      });
    }
  }

  goBack(): void {
    this.router.navigate(['/principal']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}