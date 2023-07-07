import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApplicationRoutingModule } from './application-routing.module';
import { ApplicationsComponent } from '../applications.component';
import { CarouselModule } from 'primeng/carousel';

@NgModule({
    imports: [
        CommonModule,
        ApplicationRoutingModule,
        CarouselModule,

    ],
    declarations: [ApplicationsComponent]
})
export class ApplicationModule { }