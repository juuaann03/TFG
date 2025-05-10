import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss'
})
export class RegisterComponent {
  registerForm: FormGroup;
  error: string | null = null;
  isLoading = false;
  @Output() closeModal = new EventEmitter<void>();

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private router: Router
  ) {
    this.registerForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  submitRegister(): void {
    if (this.registerForm.valid) {
      this.isLoading = true;
      this.error = null;
      const { name, email, password } = this.registerForm.value;
      this.apiService.post<any>('usuarios', {
        nombre: name,
        correo: email,
        contrasena: password,
        rol: 'usuario'
      }).subscribe({
        next: (response) => {
          localStorage.setItem('token', response.token);
          localStorage.setItem('rol', response.rol);
          this.registerForm.reset();
          this.isLoading = false;
          this.closeModal.emit();
          this.router.navigate(['/principal']);
        },
        error: (err) => {
          this.error = 'Error al crear cuenta: ' + (err.error?.detail || err.message);
          this.isLoading = false;
        }
      });
    }
  }
}