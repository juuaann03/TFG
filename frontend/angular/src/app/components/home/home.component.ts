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
  introText: string = '';
  placeholderText: string = '';
  userPrompt: string = ''; 


  private introTexts: string[] = [
    '¿Qué quieres jugar, un shooter para PS4? ¿Un clásico de Nintendo? Nuestros agentes te ayudarán a encontrar los juegos que mejor se adaptan a tus necesidades. Pregúntales lo que quieras.',
    '¿Buscas un RPG épico para PC? ¿O tal vez un juego de plataformas para Switch? Describe lo que quieres y te recomendaremos lo mejor.',
    '¿Te apetece un juego de aventuras en Xbox? ¿O un indie relajante? Nuestros agentes tienen la recomendación perfecta para ti.',
    '¿Quieres un multijugador para PS5? ¿O un clásico retro? Dinos tus gustos y encontraremos tu próximo juego favorito.',
    '¿Un juego de estrategia para PC? ¿O algo rápido para móvil? Pregunta lo que quieras y te sorprenderemos con las mejores recomendaciones.'
  ];

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
    private router: Router
  ) {
    this.recommendationForm = this.fb.group({
      prompt: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    this.isDarkMode = localStorage.getItem('theme') === 'dark';
    this.updateDarkMode();
    this.introText = this.introTexts[Math.floor(Math.random() * this.introTexts.length)];
    this.placeholderText = this.placeholderTexts[Math.floor(Math.random() * this.placeholderTexts.length)];
  }

  submitRecommendation(): void {
    if (this.recommendationForm.valid) {
      this.recommendations = null;
      this.error = null;
      this.isLoading = true;
      const prompt = this.recommendationForm.get('prompt')?.value;
      this.userPrompt = prompt; // Almacenar el prompt antes de resetear
      this.apiService.post<any>('recomendar', { descripcionUsuario: prompt }).subscribe({
        next: (response) => {
          this.recommendations = response.recomendaciones;
          this.error = null;
          this.recommendationForm.reset();
          this.isLoading = false;
        },
        error: (err) => {
          console.log('Error completo:', err);
          const errorDetail = err.error?.detail || err.message;
          this.error = `Error al obtener la recomendación: ${typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail)}`;
          this.recommendations = null;
          this.isLoading = false;
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
    localStorage.setItem('theme', this.isDarkMode ? 'dark' : 'light');
    this.updateDarkMode();
  }

  openAuthModal(mode: 'login' | 'register'): void {
    this.authMode = mode;
    this.showAuthModal = true;
  }

  closeAuthModal(): void {
    this.showAuthModal = false;
    this.authMode = null;
  }

  private updateDarkMode(): void {
    document.documentElement.classList.toggle('dark', this.isDarkMode);
  }
}