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

**Fecha de emisión (de una OC)**:
Día en que se creó la OC; acompaña a su folio y no cambia aunque la OC se edite después.
_Avoid_: fecha de modificación, vigencia

**Entrada**:
Movimiento de almacén que suma existencias en el almacén principal; su referencia lleva el folio del documento que la origina.
_Avoid_: ingreso, recepción (a secas)

**Conciliación de OC**:
Comparación de lo pedido en cada partida de una OC contra las entradas que llegaron con su folio.
_Avoid_: match, cruce

**Partida**:
Renglón de una OC con un producto o servicio, su cantidad y su precio unitario; está *ligada* cuando apunta a un producto del inventario.
_Avoid_: ítem, item, renglón

**Solicitud de OC**:
Petición interna de compra que, al aprobarse, se convierte en OC; sus partidas pasan a la OC.
_Avoid_: requisición, PO application

## SGI / Documentos

**Formato**:
Documento controlado por SGI que rige un tipo de documento impreso; tiene código (el folio del formato, p. ej. `FO-COM-04`), revisión e inicio de vigencia, que van en el encabezado. Su código no es el folio del documento que se imprime (OC, SM, remisión), ni su vigencia es la fecha de emisión de ese documento.
_Avoid_: folio (a secas) para el código del formato, fecha de emisión para la vigencia del formato, ISO form

## RH / Nómina

**Quincena**:
Periodo de pago de nómina: primera (Q1) o segunda (Q2) mitad de un mes, escrito como `2026-10-Q1`.
_Avoid_: periodo, key
