import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { LanzamientosService } from '../../services/lanzamientos.service';
import { Router, RouterModule } from '@angular/router';
import { Recomendacion } from '../../models/recomendacion';
import { ProximoLanzamiento } from '../../models/proximo-lanzamiento';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface JuegoRecomendado {
  nombre: string;
  imagen: string;
}

interface Conversacion {
  pregunta?: string;
  juegos?: JuegoRecomendado[];
}

interface HistorialResponse {
  historialConversaciones?: Conversacion[];
}

@Component({
  selector: 'app-principal',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule],
  templateUrl: './principal.component.html',
  styleUrls: ['./principal.component.scss']
})
export class PrincipalComponent implements OnInit, OnDestroy {
  recomendacionForm: FormGroup;
  recomendaciones: Recomendacion[] = [];
  nuevaRecomendacion: Recomendacion[] = [];
  proximosLanzamientos: ProximoLanzamiento[] = [];
  nombreUsuario: string | null = null;
  error: string | null = null;
  isLoading = false; // Para Próximos Lanzamientos
  isLoadingRecomendaciones = false; // Para Últimas Recomendaciones
  isLoadingRecomendacion = false; // Para Recomendación Personalizada
  isDarkMode = false;
  placeholderText: string = '';
  private destroy$ = new Subject<void>();

  private placeholderTexts: string[] = [
    'Ejemplo: Quiero un juego de aventuras para PS5',
    'Ejemplo: Busco un shooter multijugador para Xbox',
    'Ejemplo: Quiero un RPG para Nintendo Switch',
    'Ejemplo: Busco un juego indie para PC',
    'Ejemplo: Quiero un juego de puzzles para móvil'
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private lanzamientosService: LanzamientosService,
    private router: Router
  ) {
    this.recomendacionForm = this.fb.group({
      peticion: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.isDarkMode = localStorage.getItem('theme') === 'dark';
    document.documentElement.classList.toggle('dark', this.isDarkMode);

    this.nombreUsuario = localStorage.getItem('nombre') || null;

    this.placeholderText = this.placeholderTexts[Math.floor(Math.random() * this.placeholderTexts.length)];

    this.cargarUltimasRecomendaciones();
    this.cargarProximosLanzamientos();
  }

  toggleTheme(): void {
    this.isDarkMode = !this.isDarkMode;
    document.documentElement.classList.toggle('dark', this.isDarkMode);
    localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
  }

  cargarUltimasRecomendaciones(): void {
    const correo = localStorage.getItem('correo') || '';
    if (!correo) {
      this.error = 'No se encontró el correo del usuario';
      return;
    }

    this.isLoadingRecomendaciones = true;
    this.apiService.get<HistorialResponse>(`usuarios/porCorreo/${correo}/optativosConHistorial`).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response: HistorialResponse) => {
        const historial = (response.historialConversaciones || []).slice().reverse();
        const recomendacionesSinFiltrar = historial
          .filter(conv => conv.juegos && conv.juegos.length > 0)
          .flatMap(conv => (conv.juegos || []).map(juego => ({
            nombre: juego.nombre || 'Juego desconocido',
            imagen: juego.imagen || 'https://via.placeholder.com/150'
          })));

        // Filtrar duplicados en Últimas Recomendaciones basados en el nombre
        const nombresVistos = new Set<string>();
        this.recomendaciones = recomendacionesSinFiltrar
          .filter(juego => {
            if (nombresVistos.has(juego.nombre)) {
              return false;
            }
            nombresVistos.add(juego.nombre);
            return true;
          })
          .slice(0, 6); // Limitar a 6 recomendaciones

        this.isLoadingRecomendaciones = false;
      },
      error: (err: any) => {
        this.error = 'Error al cargar recomendaciones: ' + (err.error?.detail || err.message);
        this.isLoadingRecomendaciones = false;
      }
    });
  }

  cargarProximosLanzamientos(): void {
    const correo = localStorage.getItem('correo') || '';
    if (!correo) {
      this.error = 'No se encontró el correo del usuario';
      return;
    }

    this.isLoading = true;
    this.lanzamientosService.getProximosLanzamientos(correo).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (lanzamientos: ProximoLanzamiento[]) => {
        // Filtrar duplicados en Próximos Lanzamientos basados en el título
        const titulosVistos = new Set<string>();
        this.proximosLanzamientos = lanzamientos.filter(juego => {
          if (titulosVistos.has(juego.titulo)) {
            return false;
          }
          titulosVistos.add(juego.titulo);
          return true;
        });

        this.isLoading = false;
      },
      error: (err: any) => {
        this.error = 'Error al cargar próximos lanzamientos: ' + (err.message || 'Error desconocido');
        this.isLoading = false;
      }
    });
  }

  submitRecomendacion(): void {
    if (this.recomendacionForm.valid) {
      this.isLoadingRecomendacion = true;
      this.error = null;
      const correo = localStorage.getItem('correo') || '';
      if (!correo) {
        this.error = 'No se encontró el correo del usuario';
        this.isLoadingRecomendacion = false;
        return;
      }

      const peticion = this.recomendacionForm.value.peticion;
      this.apiService.post<Recomendacion[]>(`recomendaciones/personalizada/${correo}`, { peticion }).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (response: Recomendacion[]) => {
          // Filtrar duplicados en Nueva Recomendación basados en el nombre
          const nombresVistos = new Set<string>();
          this.nuevaRecomendacion = response
            .filter(juego => {
              if (nombresVistos.has(juego.nombre || '')) {
                return false;
              }
              nombresVistos.add(juego.nombre || '');
              return true;
            })
            .map((juego: Recomendacion) => ({
              nombre: juego.nombre || 'Juego desconocido',
              imagen: juego.imagen || 'https://via.placeholder.com/150',
              genero: juego.genero || 'Desconocido',
              plataformas: juego.plataformas || 'Desconocido',
              razon: juego.razon || 'No especificado'
            }));

          this.recomendacionForm.reset();
          this.isLoadingRecomendacion = false;
          this.cargarUltimasRecomendaciones();
        },
        error: (err: any) => {
          this.error = 'Error al generar recomendación: ' + (err.error?.detail || err.message);
          this.isLoadingRecomendacion = false;
        }
      });
    }
  }

  goToSettings(): void {
    this.router.navigate(['/ajustes-cuenta']);
  }

  logout(): void {
    // Limpiar datos de la sesión en localStorage
    localStorage.removeItem('correo');
    localStorage.removeItem('nombre');
    // Opcional: Limpiar el tema si no quieres que persista
    // localStorage.removeItem('theme');

    // Redirigir a la página de home
    this.router.navigate(['/home']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}