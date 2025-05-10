import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router, RouterModule } from '@angular/router';
import { Recomendacion } from '../../models/recomendacion';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

interface Conversacion {
  pregunta?: string;
  respuesta?: string;
  fecha?: string;
  contexto?: string;
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
  recomendaciones: Recomendacion[] = []; // Para el historial (Últimas Recomendaciones)
  nuevaRecomendacion: Recomendacion[] = []; // Para la nueva recomendación personalizada
  ultimosLanzamientos: Recomendacion[] = [
    { nombre: 'Juego 1', imagen: 'https://via.placeholder.com/150' },
    { nombre: 'Juego 2', imagen: 'https://via.placeholder.com/150' },
    { nombre: 'Juego 3', imagen: 'https://via.placeholder.com/150' }
  ]; // Placeholder
  nombreUsuario: string | null = null; // Nombre del usuario
  error: string | null = null;
  isLoading = false;
  isDarkMode = false;
  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    this.recomendacionForm = this.fb.group({
      peticion: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    // Cargar tema desde localStorage
    this.isDarkMode = localStorage.getItem('theme') === 'dark';
    document.documentElement.classList.toggle('dark', this.isDarkMode);

    // Obtener nombre del usuario desde localStorage
    this.nombreUsuario = localStorage.getItem('nombre') || null;

    // Obtener historial de recomendaciones
    this.cargarUltimasRecomendaciones();
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

    this.apiService.get<HistorialResponse>(`usuarios/porCorreo/${correo}/optativosConHistorial`).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: (response: HistorialResponse) => {
        const historial = (response.historialConversaciones || []).slice().reverse(); // Invertir para mostrar más recientes primero
        this.recomendaciones = historial
          .filter(conv => conv.respuesta)
          .flatMap(conv => {
            try {
              const juegos = JSON.parse(conv.respuesta || '[]');
              return juegos.map((juego: any) => ({
                nombre: juego.nombre || 'Juego desconocido',
                imagen: juego.imagen || 'https://via.placeholder.com/150',
                genero: juego.genero || 'Desconocido',
                plataformas: juego.plataformas || 'Desconocido',
                razon: juego.razon || 'No especificado'
              }));
            } catch (e) {
              console.error('Error al parsear respuesta:', e);
              return [];
            }
          })
          .slice(0, 6); // Limitar a 6 recomendaciones
      },
      error: (err: any) => {
        this.error = 'Error al cargar recomendaciones: ' + (err.error?.detail || err.message);
      }
    });
  }

  submitRecomendacion(): void {
    if (this.recomendacionForm.valid) {
      this.isLoading = true;
      this.error = null;
      const correo = localStorage.getItem('correo') || '';
      if (!correo) {
        this.error = 'No se encontró el correo del usuario';
        this.isLoading = false;
        return;
      }

      const peticion = this.recomendacionForm.value.peticion;
      this.apiService.post<Recomendacion[]>(`recomendaciones/personalizada/${correo}`, { peticion }).pipe(
        takeUntil(this.destroy$)
      ).subscribe({
        next: (response: Recomendacion[]) => {
          this.nuevaRecomendacion = response.map((juego: Recomendacion) => ({
            nombre: juego.nombre || 'Juego desconocido',
            imagen: juego.imagen || 'https://via.placeholder.com/150',
            genero: juego.genero || 'Desconocido',
            plataformas: juego.plataformas || 'Desconocido',
            razon: juego.razon || 'No especificado'
          }));
          this.recomendacionForm.reset();
          this.isLoading = false;
          // Recargar historial para actualizar Últimas Recomendaciones
          this.cargarUltimasRecomendaciones();
        },
        error: (err: any) => {
          this.error = 'Error al generar recomendación: ' + (err.error?.detail || err.message);
          this.isLoading = false;
        }
      });
    }
  }

  goToSettings(): void {
    this.router.navigate(['/account-settings']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}