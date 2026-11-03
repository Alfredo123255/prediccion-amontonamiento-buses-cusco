# 📄 Descripción de los Datasets

Este repositorio contiene dos conjuntos de datos relacionados con el registro y análisis de tiempos de control y datos georreferenciados de vehículos.  

## Dataset 1: Tiempos de Control (`Times.csv`)

Este dataset registra los tiempos de control por vuelta de los vehículos.

| Columna          | Descripción                                                                |
|-----------------|-----------------------------------------------------------------------------|
| `id`            | Identificador único del registro.                                           |
| `lap`           | Número de vuelta o recorrido asociado al registro.                          |
| `date`          | Fecha del registro (`YYYY-MM-DD`).                                          |
| `time`          | Hora exacta del registro (`HH:MM:SS`).                                      |
| `start_time`    | Hora de inicio del tramo o evento.                                          |
| `end_time`      | Hora de finalización del tramo o evento.                                    |
| `difference_time`| Diferencia entre `end_time` y `start_time` (tiempo total del tramo).       |
| `vehicle_id_id` | Identificador del vehículo asociado al registro (llave foránea).            |


## Dataset 2: Datos Georreferenciados (`Monitoring.csv`)

Este dataset contiene los datos de localización de los vehículos.

| Columna         | Descripción                                                                |
|----------------|-----------------------------------------------------------------------------|
| `id`           | Identificador único del registro.                                           |
| `date`         | Fecha del registro (`YYYY-MM-DD`).                                          |
| `time`         | Hora exacta del registro (`HH:MM:SS`).                                      |
| `lap`          | Número de vuelta asociado al registro.                                      |
| `latitude`     | Latitud en coordenadas decimales.                                           |
| `longitude`    | Longitud en coordenadas decimales.                                          |
| `speed`        | Velocidad del vehículo (en km/h o m/s, según la fuente de datos).           |
| `bearing`      | Rumbo o dirección de desplazamiento en grados (0° = Norte).                 |
| `vehicle_id_id`| Identificador del vehículo asociado al registro (llave foránea).            |
