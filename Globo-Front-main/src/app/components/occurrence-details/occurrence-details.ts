import { Component, EventEmitter, Input, Output, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api';
import { ToastService } from '../../services/toast.service'; // <--- Importar

@Component({
  selector: 'app-occurrence-details',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './occurrence-details.html',
  styleUrls: ['./occurrence-details.scss']
})
export class OccurrenceDetailsComponent implements OnChanges {
  @Input() occurrenceId: number | null = null;
  @Output() close = new EventEmitter<void>();
  @Output() statusChanged = new EventEmitter<void>();

  occurrence: any = null;
  loading = false;
  processing = false; // Controla o estado dos botões de ação

  constructor(
    private api: ApiService,
    private toast: ToastService // <--- Injetar
  ) {}

  ngOnChanges(changes: SimpleChanges) {
    if (changes['occurrenceId'] && this.occurrenceId) {
      this.loadDetails(this.occurrenceId);
    }
  }

  loadDetails(id: number) {
    this.loading = true;
    this.occurrence = null;
    
    this.api.getOccurrenceById(id).subscribe({
      next: (data) => {
        this.occurrence = data;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.toast.show('Erro ao carregar detalhes.', 'error');
        this.loading = false;
        this.onClose();
      }
    });
  }

  validate() {
    if (!this.occurrence) return;
    this.processing = true;
    
    this.api.updateStatus(this.occurrence.id, 'Aprovado').subscribe({
      next: () => {
        this.toast.show(`Ocorrência #${this.occurrence.id} aprovada!`, 'success');
        this.statusChanged.emit();
        this.onClose();
      },
      error: () => {
        this.toast.show('Erro ao aprovar ocorrência.', 'error');
        this.processing = false;
      }
    });
  }

  reject() {
    if (!this.occurrence) return;
    this.processing = true;

    this.api.updateStatus(this.occurrence.id, 'Rejeitado').subscribe({
      next: () => {
        this.toast.show(`Ocorrência #${this.occurrence.id} rejeitada.`, 'info');
        this.statusChanged.emit();
        this.onClose();
      },
      error: () => {
        this.toast.show('Erro ao rejeitar ocorrência.', 'error');
        this.processing = false;
      }
    });
  }

  onClose() {
    this.close.emit();
    this.occurrence = null;
    this.processing = false;
  }
}