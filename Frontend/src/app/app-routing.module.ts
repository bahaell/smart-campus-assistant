import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { NavigationBotComponent } from './components/navigation-bot/navigation-bot.component';
import { LostAndFoundComponent } from './components/lost-and-found/lost-and-found.component';
import { ServicesComponent } from './components/services/services.component';
import { AboutComponent } from './components/about/about.component';
import { ComingSoonComponent } from './components/coming-soon/coming-soon.component';

const routes: Routes = [
  { path: '', component: NavigationBotComponent },
  { path: 'lost-and-found', component: LostAndFoundComponent },
  { path: 'services', component: ServicesComponent },
  { path: 'about', component: AboutComponent },
  { path: 'coming-soon', component: ComingSoonComponent }

];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
