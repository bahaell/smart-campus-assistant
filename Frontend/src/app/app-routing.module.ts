import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { NavigationBotComponent } from './components/navigation-bot/navigation-bot.component';
import { LostAndFoundComponent } from './components/lost-and-found/lost-and-found.component';

const routes: Routes = [
  { path: '', component: NavigationBotComponent },
  { path: 'lost-and-found', component: LostAndFoundComponent },
  { path: '**', redirectTo: '' }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
