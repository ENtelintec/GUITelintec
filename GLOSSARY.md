# Back-office Telintec

Vocabulario del negocio que maneja el API interno de Telintec (RH, almacén, compras, administración, SGI). Solo términos propios del dominio; los detalles de implementación viven en `docs/`.

## RH / Encuestas

**Proceso eva 360**:
Evaluación de desempeño de una persona hecha desde varias perspectivas (2 a 4), una por rol, que RH abre y cierra.
_Avoid_: encuesta 360, evaluación (a secas)

**Perspectiva**:
La evaluación que llena un evaluador desde su rol dentro de un proceso eva 360.
_Avoid_: encuesta, cuestionario individual

**Rol del evaluador**:
Relación del evaluador con el evaluado: Autoevaluación, Jefe Inmediato, Colega o Subordinado; un evaluador por rol en cada proceso.
_Avoid_: Jefe directo, Par, self/superior/peer/subordinate en textos para usuarios

**Perspectiva respondida**:
Una perspectiva con todas sus competencias contestadas; una parcial cuenta como pendiente.

**Proceso cerrado**:
Proceso eva 360 que RH da por definitivo, aunque falte alguna perspectiva; mientras está abierto, su reporte es preliminar.
_Avoid_: completo, terminado

## Compras / Almacén

**Orden de compra (OC)**:
Pedido formal a un proveedor, con folio propio y partidas de productos o servicios.
_Avoid_: PO, purchase order (en textos para usuarios)

**Entrada**:
Movimiento de almacén que suma existencias en el almacén principal; su referencia lleva el folio del documento que la origina.
_Avoid_: ingreso, recepción (a secas)

**Conciliación de OC**:
Comparación de lo pedido en cada partida de una OC contra las entradas que llegaron con su folio.
_Avoid_: match, cruce

## RH / Nómina

**Quincena**:
Periodo de pago de nómina: primera (Q1) o segunda (Q2) mitad de un mes, escrito como `2026-10-Q1`.
_Avoid_: periodo, key
