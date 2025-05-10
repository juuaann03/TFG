import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import * as CryptoJS from 'crypto-js';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  loginForm: FormGroup;
  error: string | null = null;
  isLoading = false;
  @Output() closeModal = new EventEmitter<void>();

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  submitLogin(): void {
    if (this.loginForm.valid) {
      this.isLoading = true;
      this.error = null;
      const { email, password } = this.loginForm.value;
      // Cifrar la contraseña para protegerla en tránsito
      const cryptoKey = import.meta.env.VITE_CRYPTO_KEY;
      const encryptedPassword = CryptoJS.AES.encrypt(password, cryptoKey).toString();
      this.apiService.post<any>('auth/login', { correo: email, contrasena: encryptedPassword }).subscribe({
        next: (response) => {
          localStorage.setItem('token', response.token);
          localStorage.setItem('rol', response.rol);
          this.loginForm.reset();
          this.isLoading = false;
          this.closeModal.emit();
          this.router.navigate(['/principal']);
        },
        error: (err) => {
          this.error = 'Error al iniciar sesión: ' + (err.error?.detail || err.message);
          this.isLoading = false;
        }
      });
    }
  }
}