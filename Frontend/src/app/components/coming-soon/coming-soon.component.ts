import { Component, OnDestroy, OnInit } from '@angular/core';

@Component({
  selector: 'app-coming-soon',
  templateUrl: './coming-soon.component.html',
  styleUrls: ['./coming-soon.component.css']
})
export class ComingSoonComponent implements OnInit, OnDestroy {
  countdown = {
    days: 74,
    hours: 12,
    minutes: 45,
    seconds: 0
  };

  private timer: any;

  get days() {
    return this.countdown.days;
  }

  get hours() {
    return this.countdown.hours;
  }

  get minutes() {
    return this.countdown.minutes;
  }

  get seconds() {
    return this.countdown.seconds;
  }

  ngOnInit() {
    this.startCountdown();
  }

  ngOnDestroy() {
    if (this.timer) {
      clearInterval(this.timer);
    }
  }

  private startCountdown() {
    this.timer = setInterval(() => {
      if (this.countdown.seconds > 0) {
        this.countdown.seconds--;
      } else {
        this.countdown.seconds = 59;
        if (this.countdown.minutes > 0) {
          this.countdown.minutes--;
        } else {
          this.countdown.minutes = 59;
          if (this.countdown.hours > 0) {
            this.countdown.hours--;
          } else {
            this.countdown.hours = 23;
            if (this.countdown.days > 0) {
              this.countdown.days--;
            } else {
              clearInterval(this.timer);
            }
          }
        }
      }
    }, 1000);
  }
}
