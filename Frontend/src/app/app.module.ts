import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { NavigationBotComponent } from './components/navigation-bot/navigation-bot.component';
import { LostAndFoundComponent } from './components/lost-and-found/lost-and-found.component';
import { FooterComponent } from './components/footer/footer.component';
import { LucideAngularModule, Image, MapPin, User, Calendar, ChevronUp, ChevronDown, Lightbulb, Send, Mail, Phone, Search, Bot } from 'lucide-angular';
import { HeaderComponent } from './components/header/header.component';
import { ServicesComponent } from './components/services/services.component';
import { AboutComponent } from './components/about/about.component';
import search from 'lucide-angular/icons/search';
import { ComingSoonComponent } from './components/coming-soon/coming-soon.component';

@NgModule({
  declarations: [
    AppComponent,
    NavigationBotComponent,
    LostAndFoundComponent,
    FooterComponent,
    HeaderComponent,
    ServicesComponent,
    AboutComponent,
    ComingSoonComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    FormsModule,
    LucideAngularModule.pick({Search, Bot , Mail, Phone , Send, MapPin, User, Calendar, ChevronDown, ChevronUp, Lightbulb, Image })
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
