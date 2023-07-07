import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AdvancedRoutingModule } from './advanced.routing.module';
import { AdvancedComponent } from '../advanced.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AccordionModule } from 'primeng/accordion';
import { SliderModule } from 'primeng/slider';
import { DialogModule } from 'primeng/dialog';
import { TooltipModule } from 'primeng/tooltip';
import { MultiSelectModule } from 'primeng/multiselect';
import { DropdownModule } from 'primeng/dropdown';
@NgModule({
    imports: [
        CommonModule,
        AdvancedRoutingModule,
        FormsModule,
        ReactiveFormsModule,
        AccordionModule,
        SliderModule,
        DialogModule,
        TooltipModule,
        MultiSelectModule,
        DropdownModule
    ],
    declarations: [AdvancedComponent]
})
export class AdvancedModule { }