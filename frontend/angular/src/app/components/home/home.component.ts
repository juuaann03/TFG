import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import { LoginComponent } from '../login/login.component';
import { RegisterComponent } from '../register/register.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    LoginComponent,
    RegisterComponent
  ],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {
  recommendationForm: FormGroup;
  recommendations: any[] | null = null;
  error: string | null = null;
  isDarkMode = false;
  showAuthModal = false;
  authMode: 'login' | 'register' | null = null;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    this.recommendationForm = this.fb.group({
      prompt: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.isDarkMode = localStorage.getItem('darkMode') === 'true';
    this.updateDarkMode();
  }

  submitRecommendation(): void {
    if (this.recommendationForm.valid) {
      this.recommendations = null; // Limpiar recomendaciones anteriores
      this.error = null; // Limpiar errores anteriores
      this.isLoading = true; // Activar carga
      const prompt = this.recommendationForm.get('prompt')?.value;
      this.apiService.post<any>('recomendar', { descripcionUsuario: prompt }).subscribe({
        next: (response) => {
          this.recommendations = response.recomendaciones;
          this.error = null;
          this.recommendationForm.reset();
          this.isLoading = false; // Desactivar carga
        },
        error: (err) => {
          console.log('Error completo:', err);
          const errorDetail = err.error?.detail || err.message;
          this.error = `Error al obtener la recomendación: ${typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail)}`;
          this.recommendations = null;
          this.isLoading = false; // Desactivar carga
        }
      });
    }
  }

  clearRecommendation(): void {
    this.recommendations = null;
    this.error = null;
    this.recommendationForm.reset();
  }

  toggleDarkMode(): void {
    this.isDarkMode = !this.isDarkMode;
    localStorage.setItem('darkMode', this.isDarkMode.toString());
    this.updateDarkMode();
  }

  openAuthModal(): void {
    this.showAuthModal = true;
    this.authMode = null;
  }

  closeAuthModal(): void {
    this.showAuthModal = false;
    this.authMode = null;
  }

  selectAuthMode(mode: 'login' | 'register'): void {
    this.authMode = mode;
  }

  private updateDarkMode(): void {
    if (this.isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }
}