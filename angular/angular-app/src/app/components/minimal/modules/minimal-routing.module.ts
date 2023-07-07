import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MinimalComponent } from '../minimal.component';



const routes: Routes = [
    {
        path: '',
        component: MinimalComponent
    }
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class MinimalRoutingModule { }