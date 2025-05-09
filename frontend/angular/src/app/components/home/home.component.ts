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
  recommendations: any[] | null = null; // Cambiar a lista
  error: string | null = null;
  isDarkMode = false;
  showAuthModal = false;
  authMode: 'login' | 'register' | null = null;

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
      const prompt = this.recommendationForm.get('prompt')?.value;
      this.apiService.post<any>('recomendar', { descripcionUsuario: prompt }).subscribe({
        next: (response) => {
          this.recommendations = response.recomendaciones; // Usar 'recomendaciones'
          this.error = null;
          this.recommendationForm.reset();
        },
        error: (err) => {
          console.log('Error completo:', err); // Para depurar
          this.error = 'Error al obtener la recomendación: ' + (err.error?.detail || err.message);
          this.recommendations = null;
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