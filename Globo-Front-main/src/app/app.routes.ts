import { Routes } from '@angular/router';
import { MonitorComponent } from './pages/monitor/monitor';
import { DashboardComponent } from './pages/dashboard/dashboard';
import { HistoryComponent } from './pages/history/history';
import { InitializerComponent } from './components/initializer/initializer.component';

export const routes: Routes = [
  { path: '', component: InitializerComponent, pathMatch: 'full' },
  { path: 'monitor', component: MonitorComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'historico', component: HistoryComponent }
];