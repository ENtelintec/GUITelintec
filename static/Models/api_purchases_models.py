# -*- coding: utf-8 -*-
__author__ = "Edisson Naula"
__date__ = "$ 14/nov/2024  at 16:15 $"

from wtforms.fields.numeric import IntegerField

from static.Models.api_models import datetime_filter
from static.constants import api
from flask_restx import fields
from wtforms.fields.datetime import DateTimeField
from wtforms.validators import InputRequired, number_range
from wtforms import (
    FormField,
    StringField,
    URLField,
    FloatField,
    validators,
    BooleanField,
)
from wtforms.fields.list import FieldList
from wtforms.form import Form


purchase_metadata_model = api.model(
    "PurchaseMetadata",
    {
        "name": fields.String(required=True, description="The name"),
        "quantity": fields.Integer(required=True, description="The quantity"),
        "supplier": fields.String(required=True, description="The supplier"),
        "link": fields.String(required=True, description="The link"),
        "comments": fields.String(required=True, description="The comments"),
        "date_required": fields.String(required=True, description="The date required"),
    },
)

timestamp_model = api.model(
    "TimestampP",
    {
        "timestamp": fields.String(
            required=True, description="The quotation timestamp"
        ),
        "comment": fields.String(required=True, description="The quotation comment"),
    },
)

timestamps_purchase_model = api.model(
    "TimestampPurchase",
    {
        "complete": fields.Nested(timestamp_model, required=False),
        "update": fields.List(fields.Nested(timestamp_model), required=False),
    },
)


items_po_model = api.model(
    "ItemsPO",
    {
        "id": fields.Integer(required=False, description="The item id", example=0),
        "description": fields.String(
            required=True, description="The name or desciption"
        ),
        "quantity": fields.Float(required=True, description="The quantity"),
        "unit_price": fields.Float(required=True, description="The unit price"),
        "brand": fields.String(required=True, description="The brand"),
        "category": fields.String(required=True, description="The supplier"),
        "id_inventory": fields.Integer(
            required=True, description="The inventory id", example=0
        ),
        "url": fields.String(
            required=True, description="The url", example="https://www.example.com"
        ),
        "n_parte": fields.String(
            required=True, description="The part number", example="1234567890"
        ),
        "duration_services": fields.String(
            required=False, description="The duration services", example="2024-03-01"
        ),
        "purchase_id": fields.Integer(
            required=False, description="The purchase id", example=0
        ),
        "tool": fields.Integer(
            required=True, description="The state if is a tool 1", example=0
        ),
        "comment": fields.String(
            required=False, description="The comment", example="Some comment"
        ),
        "currency": fields.String(
            required=False, description="The currency", example="MXN"
        ),
    },
)

history_purchase_model = api.model(
    "HistoryPurchase",
    {
        "user": fields.Integer(required=True, description="The user id", example=1),
        "event": fields.String(
            required=True, description="The event", example="Some event"
        ),
        "date": fields.String(
            required=True, description="The date", example="2024-03-01"
        ),
        "comment": fields.String(
            required=True, description="The comment", example="Some comment"
        ),
    },
)


metadata_telintec_order_model = api.model(
    "MetadataTelintecOrder",
    {
        "name": fields.String(
            required=True, description="The name", example="TELINTEC S.A. DE CV"
        ),
        "address_invoice": fields.String(
            required=True,
            description="The address of the invoice",
            example="Av. Lázaro Cárdenas 306 1er piso oficina A-1 Col. Residencial San Agustín San Pedro Garza García, NL, C.P. 66260",
        ),
        "address_comercial": fields.String(
            required=True,
            description="The address of the comercial",
            example="Calle La barca 140 Col. Mitras Sur C.P.64020 Monterrey, N.L CP 64030 Monterrey, N.L.",
        ),
        "phone": fields.String(
            required=True, description="The phone", example="1234567890"
        ),
        "email": fields.String(
            required=True, description="The email", example="email@email.com"
        ),
        "rfc": fields.String(
            required=True, description="The RFC", example="RFC1234567890"
        ),
        "responsable": fields.String(
            required=True,
            description="The person responsable name",
            example="Carolina Torres",
        ),
    },
)

metadata_supplier_model = api.model(
    "MetadataSupplier",
    {
        "name": fields.String(
            required=True, description="The name", example="TELINTEC S.A. DE CV"
        ),
        "address_invoice": fields.String(
            required=True,
            description="The address of the invoice",
            example="Av. Lázaro Cárdenas 306 1er piso oficina A-1 Col. Residencial San Agustín San Pedro Garza García, NL, C.P. 66260",
        ),
        "rfc": fields.String(
            required=True, description="The RFC", example="RFC1234567890"
        ),
        "salesman": fields.String(
            required=True,
            description="The person salesanan name",
            example="Carolina Torres",
        ),
        "payment_method": fields.String(
            required=True, description="The payment method"
        ),
        "delivery_conditions": fields.String(
            required=True, description="The delivery conditions"
        ),
        "delivery_address": fields.String(
            required=True,
            description="The delivery address",
            example="Calle La barca 140 Col. Mitras Sur C.P.64020 Monterrey, N.L CP 64030 Monterrey, N.L.",
        ),
        "transport": fields.String(
            required=True, description="The transport", example="proveedor"
        ),
        "insurance": fields.String(
            required=True, description="The insurance", example="proveedor"
        ),
        "guarantee": fields.String(
            required=True, description="The guarantee", example="proveedor"
        ),
    },
)

pos_application_post_model = api.model(
    "PurchaseOrderApplicationPost",
    {
        "reference": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "sm_id": fields.Integer(
            required=False, description="The quotation sm id", example=1
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
    },
)


pos_application_put_model = api.model(
    "PurchaseOrderApplicationPut",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "reference": fields.String(
            required=True,
            description="The application reference",
            example="alm-xxx-xx",
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "created_by": fields.Integer(
            required=True, description="The quotation created by", example=1
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
    },
)

purchase_order_post_model = api.model(
    "PurchaseOrderPost",
    {
        "folio": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "sm_id": fields.Integer(
            required=False, description="The quotation sm id", example=1
        ),
        "supplier": fields.Integer(
            required=True, description="The supplier id", example=1
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "time_delivery": fields.String(
            required=True, description="The quotation time delivery", example="3 weeks"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
        "metadata_telintec": fields.Nested(
            metadata_telintec_order_model, required=True
        ),
        "metadata_supplier": fields.Nested(metadata_supplier_model, required=True),
        "order_quotation": fields.String(
            required=False,
            description="The order quotation document",
            example="base64encodedstring",
        ),
    },
)


purchase_order_put_model = api.model(
    "PurchaseOrderPut",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "folio": fields.String(
            required=True,
            description="The quotation creation date",
            example="2024-03-01",
        ),
        "supplier": fields.Integer(
            required=True, description="The supplier id", example=1
        ),
        "comment": fields.String(
            required=True, description="The quotation comment", example="Some comment"
        ),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "created_by": fields.Integer(
            required=True, description="The quotation created by", example=1
        ),
        "time_delivery": fields.String(
            required=True, description="The quotation time delivery", example="3 weeks"
        ),
        "items": fields.List(fields.Nested(items_po_model, required=True)),
        "metadata_telintec": fields.Nested(
            metadata_telintec_order_model, required=True
        ),
        "metadata_supplier": fields.Nested(metadata_supplier_model, required=True),
        "sm_id": fields.Integer(
            required=False, description="The quotation sm id", example=1
        ),
        "order_quotation": fields.String(
            required=False,
            description="The order quotation document",
            example="base64encodedstring",
        ),
    },
)

purchase_order_delete_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
    },
)

po_app_delete_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=4
        ),
    },
)

purchase_order_update_status_model = api.model(
    "PurchaseOrderDelete",
    {
        "id": fields.Integer(required=True, description="The quotation id", example=1),
        "history": fields.List(fields.Nested(history_purchase_model), required=True),
        "status": fields.Integer(
            required=True, description="The quotation status", example=0
        ),
        "approved": fields.Integer(
            required=True, description="The quotation approved", example=1
        ),
    },
)


quotation_activity_insert_item_model = api.model(
    "QuotationActivityItem",
    {
        "report_id": fields.Integer(
            required=False,
            description="ID de reporte asociado (si aplica)",
            example=1452,
        ),
        "description": fields.String(
            required=True,
            description="Descripción del concepto/servicio a cotizar",
            example="Calibración de sensor de presión en línea 3",
        ),
        "udm": fields.String(
            required=True,
            description="Unidad de medida",
            example="servicio",
        ),
        "quantity": fields.Float(
            required=True,
            description="Cantidad requerida",
            example=2.0,
        ),
        "unit_price": fields.Float(
            required=True,
            description="Precio unitario",
            example=1500.00,
        ),
        "item_contract_id": fields.Integer(
            # attribute="item_c_id",
            required=False,
            description="ID del del item de contrato asociado (si aplica)",
            example=321,
        ),
    },
)


quotation_activity_item_upsert_model = api.model(
    "QuotationActivityItemUpsert",
    {
        "id": fields.Integer(
            required=False,
            description=(
                "ID del ítem. Si se omite o es <= 0, se creará un nuevo ítem."
                "Si es > 0, se actualizará el ítem existente."
            ),
            example=58,
        ),
        "report_id": fields.Integer(
            required=False,
            description="ID de reporte asociado (si aplica)",
            example=1452,
        ),
        "item_contract_id": fields.Integer(
            required=False,
            description="ID del del item de contrato asociado (si aplica)",
            example=321,
        ),
        "description": fields.String(
            required=True,
            description="Descripción del concepto/servicio a cotizar",
            example="Calibración de sensor de presión en línea 3",
        ),
        "udm": fields.String(
            required=True,
            description="Unidad de medida",
            example="servicio",
        ),
        "quantity": fields.Float(
            required=True,
            description="Cantidad requerida",
            example=2.0,
        ),
        "unit_price": fields.Float(
            required=True,
            description="Precio unitario",
            example=1500.00,
        ),
        "is_erased": fields.Boolean(
            required=False,
            description="Indica si el ítem está marcado para eliminación (solo para actualizaciones)",
            example=False,
        ),
    },
)


quotation_activity_create_model = api.model(
    "QuotationActivityCreate",
    {
        "date_activity": fields.String(
            required=True,
            description="Fecha de la actividad",
            example="2026-02-25",
        ),
        "folio": fields.String(
            required=True,
            description="Folio o referencia interna de la cotización",
            example="QA-2026-00045",
        ),
        "client_id": fields.Integer(
            required=True,
            description="ID del cliente",
            example=120,
        ),
        "client_company_name": fields.String(
            required=True,
            description="Nombre de la empresa del cliente",
            example="Acme Industrial S.A. de C.V.",
        ),
        "client_contact_name": fields.String(
            required=True,
            description="Nombre del contacto del cliente",
            example="María López",
        ),
        "client_phone": fields.String(
            required=False,
            description="Teléfono del contacto del cliente",
            example="+52 81 1234 5678",
        ),
        "client_email": fields.String(
            required=False,
            description="Correo electrónico del contacto del cliente",
            example="maria.lopez@acme.com",
        ),
        "plant": fields.String(
            required=True,
            description="Planta del cliente donde se realizará la actividad",
            example="Planta Monterrey",
        ),
        "area": fields.String(
            required=True,
            description="Área dentro de la planta",
            example="Producción",
        ),
        "location": fields.String(
            required=True,
            description="Ubicación específica o referencia",
            example="Línea 3 - Nodo PZ-34",
        ),
        "general_description": fields.String(
            required=True,
            description="Descripción general de la actividad a cotizar",
            example="Servicio de mantenimiento preventivo y calibración de sensores",
        ),
        "comments": fields.String(
            required=False,
            description="Comentarios generales adicionales",
            example="Requiere acceso fuera de horario laboral.",
        ),
        "status": fields.Integer(
            required=True,
            description="Estatus de la actividad de cotización",
            example=0,
        ),
        "items": fields.List(
            fields.Nested(quotation_activity_insert_item_model),
            required=True,
            description="Lista de ítems a cotizar",
        ),
    },
)


quotation_activity_update_model = api.model(
    "QuotationActivityUpdate",
    {
        "id": fields.Integer(
            required=True,
            description="ID de la actividad de cotización a actualizar",
            example=1012,
        ),
        "date_activity": fields.String(
            required=True,
            description="Fecha de la actividad",
            example="2026-03-10",
        ),
        "folio": fields.String(
            required=True,
            description="Folio o referencia interna de la cotización",
            example="QA-2026-00045",
        ),
        "client_id": fields.Integer(
            required=True,
            description="ID del cliente",
            example=120,
        ),
        "client_company_name": fields.String(
            required=True,
            description="Nombre de la empresa del cliente",
            example="Acme Industrial S.A. de C.V.",
        ),
        "client_contact_name": fields.String(
            required=True,
            description="Nombre del contacto del cliente",
            example="María López",
        ),
        "client_phone": fields.String(
            required=False,
            description="Teléfono del contacto del cliente",
            example="+52 81 1234 5678",
        ),
        "client_email": fields.String(
            required=False,
            description="Correo electrónico del contacto del cliente",
            example="maria.lopez@acme.com",
        ),
        "plant": fields.String(
            required=True,
            description="Planta del cliente",
            example="Planta Monterrey",
        ),
        "area": fields.String(
            required=True,
            description="Área dentro de la planta",
            example="Producción",
        ),
        "location": fields.String(
            required=True,
            description="Ubicación específica",
            example="Línea 3 - Nodo PZ-34",
        ),
        "general_description": fields.String(
            required=True,
            description="Descripción general de la actividad",
            example="Servicio de mantenimiento preventivo y calibración de sensores",
        ),
        "comments": fields.String(
            required=False,
            description="Comentarios generales adicionales",
            example="Coordinar ingreso con seguridad industrial.",
        ),
        "status": fields.Integer(
            required=True,
            description="Estatus de la actividad de cotización",
            example=1,
        ),
        "items": fields.List(
            fields.Nested(quotation_activity_item_upsert_model),
            required=True,
            description=(
                "Lista de ítems a crear/actualizar. Si un ítem no trae 'id' o éste es <= 0, se crea; "
                "si 'id' > 0, se actualiza el correspondiente. La lista solo debe incluir items actualizados o por crear"
            ),
        ),
    },
)


quotation_activity_delete_model = api.model(
    "QuotationActivityDelete",
    {
        "id": fields.Integer(
            required=True,
            description="ID de la actividad de cotización a eliminar",
            example=1012,
        )
    },
)


quoatation_activity_status_update_model = api.model(
    "QuotationActivityStatusUpdate",
    {
        "id": fields.Integer(
            required=True,
            description="ID de la actividad de cotización a actualizar",
            example=1012,
        ),
        "status": fields.Integer(
            required=True,
            description="Nuevo estatus de la actividad de cotización",
            example=2,
        )
    },
)

remission_model_insert = api.model(
    "RemissionInsert",
    {
        "metadata": fields.Nested(
            api.model(
                "MetadataRemission",
                {
                    "remission_code": fields.String(
                        required=True, example="TLA0704-459"
                    ),
                    "client_id": fields.Integer(required=True, example=12),
                    "emission": fields.String(
                        required=True, example="2025-06-05 10:00:00"
                    ),
                    "user": fields.String(required=True, example="jdoe"),
                    "planta": fields.String(required=False, example="Planta Norte"),
                    "area": fields.String(required=False, example="Producción"),
                    "location": fields.String(required=False, example="Zona 3"),
                    "email": fields.String(
                        required=False, example="cliente@empresa.com"
                    ),
                    "phone": fields.String(required=False, example="8123456789"),
                    "observations": fields.String(
                        required=False, example="Entrega parcial"
                    ),
                    "printed": fields.Boolean(required=False, default=False),
                    "status": fields.Integer(required=False, default=0),
                },
            )
        ),
        "contract_id": fields.Integer(required=True, example=5),
        "items": fields.List(
            fields.Nested(
                api.model(
                    "ProductsPostRemission",
                    {
                        "quotation_item_id": fields.Integer(required=False, example=55),
                        "description": fields.String(
                            required=True, example="Placa COM 01 M2"
                        ),
                        "quantity": fields.Float(required=True, example=4),
                        "udm": fields.String(required=True, example="PZA"),
                        "price_unit": fields.Float(required=True, example=1200.00),
                    },
                )
            ),
            required=False,
        ),
    },
)


remission_model_update = api.model(
    "RemissionUpdate",
    {
        "id": fields.Integer(required=True, example=1),
        "contract_id": fields.Integer(required=False, example=5),
        "metadata": fields.Nested(
            api.model(
                "MetadataRemissionUpdate",
                {
                    "remission_code": fields.String(
                        required=True, example="TLA0704-459"
                    ),
                    "client_id": fields.Integer(required=True, example=12),
                    "emission": fields.String(
                        required=True, example="2025-06-05 10:00:00"
                    ),
                    "user": fields.String(required=True, example="jdoe"),
                    "planta": fields.String(required=False, example="Planta Norte"),
                    "area": fields.String(required=False, example="Producción"),
                    "location": fields.String(required=False, example="Zona 3"),
                    "email": fields.String(
                        required=False, example="cliente@empresa.com"
                    ),
                    "phone": fields.String(required=False, example="8123456789"),
                    "observations": fields.String(
                        required=False, example="Entrega parcial"
                    ),
                    "printed": fields.Boolean(required=False, default=False),
                    "status": fields.Integer(required=False, default=0),
                },
            )
        ),
        "items": fields.List(
            fields.Nested(
                api.model(
                    "ItemsRemissionUpdate",
                    {
                        "id": fields.Integer(required=False, example=101),
                        "quotation_item_id": fields.Integer(required=False, example=55),
                        "description": fields.String(
                            required=True, example="Placa COM 01 M2"
                        ),
                        "quantity": fields.Float(required=True, example=4),
                        "udm": fields.String(required=True, example="PZA"),
                        "price_unit": fields.Float(required=True, example=1200.00),
                    },
                )
            ),
            required=False,
        ),
        "items_to_delete": fields.List(
            fields.Nested(
                api.model(
                    "ItemsRemissionDelete",
                    {
                        "id": fields.Integer(required=True, example=101),
                    },
                )
            ),
            required=False,
        ),
        "history": fields.List(
            fields.Nested(
                api.model(
                    "RemissionHistoryEntry",
                    {
                        "timestamp": fields.String(
                            required=True, example="2025-10-27 21:00:00"
                        ),
                        "user": fields.String(required=True, example="jdoe"),
                        "action": fields.String(required=True, example="update"),
                        "comment": fields.String(
                            required=False, example="Actualización desde API"
                        ),
                    },
                )
            ),
            required=False,
        ),
    },
)


remission_model_delete = api.model(
    "RemissionDelete", {"id": fields.Integer(required=True, example=1)}
)


class HistoryPurchaseForm(Form):
    user = IntegerField("user", [InputRequired()])
    event = StringField("event", [InputRequired()])
    date = DateTimeField("date", [InputRequired()], filters=[datetime_filter])
    comment = StringField("comment", [], default="")


class ItemsPOFormPU(Form):
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = FloatField("id_inventory", [], default=0)
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")
    duration_services = StringField("duration_services", [], default="0")
    supplier = StringField("supplier", [], default="")
    purchase_id = IntegerField("purchase_id", [], default=0)
    id = IntegerField("id", [number_range(min=-1, message="Invalid id")], default=-1)
    currency = StringField("currency", [], default="MXN")
    tool = IntegerField("tool", [number_range(min=-1, max=2, message="Invalid tool")])


class ItemsPOApplicationForm(Form):
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    brand = StringField("brand", [])
    category = StringField("category", [])
    id_inventory = FloatField("id_inventory", [], default=0)
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")
    supplier = StringField("supplier", [], default="")
    purchase_id = IntegerField("purchase_id", [], default=0)
    tool = IntegerField("tool", [number_range(min=-1, max=2, message="Invalid tool")])
    comment = StringField("comment", [], default="")


class MetadataTelitencForm(Form):
    name = StringField("name", [InputRequired()])
    address_invoice = StringField("address_invoice", [InputRequired()])
    address_comercial = StringField("address_comercial", [InputRequired()])
    phone = StringField("phone", [InputRequired()])
    email = StringField("email", [InputRequired()])
    rfc = StringField("rfc", [InputRequired()])
    responsable = StringField("responsable", [InputRequired()])


class MetadataSupplierForm(Form):
    name = StringField("name", [InputRequired()])
    address_invoice = StringField("address_invoice", [InputRequired()])
    rfc = StringField("rfc", [InputRequired()])
    salesman = StringField("salesman", [InputRequired()])
    payment_method = StringField("payment_method", [InputRequired()])
    delivery_conditions = StringField("delivery_conditions", [InputRequired()])
    delivery_address = StringField("delivery_address", [InputRequired()])
    transport = StringField("transport", [InputRequired()])
    insurance = StringField("insurance", [InputRequired()])
    guarantee = StringField("guarantee", [InputRequired()])


class PurchaseOrderPostForm(Form):
    folio = StringField("folio", [InputRequired()])
    supplier = IntegerField("supplier", [InputRequired()])
    comment = StringField("comment", [])
    time_delivery = StringField("time_delivery", [], default="")
    items = FieldList(FormField(ItemsPOFormPU), "items", validators=[], default=[])
    metadata_telintec = FormField(MetadataTelitencForm)
    metadata_supplier = FormField(MetadataSupplierForm)
    sm_id = IntegerField("sm_id", [], default=0)
    order_quotation = StringField("order_quotation", [], default="")


class ItemsPOUpdateForm(Form):
    id = IntegerField("id", [number_range(min=-1, message="Invalid id")], default=-1)
    id_purchase = IntegerField("id_purchase", [], default=0)
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = IntegerField(
        "id_inventory",
        [validators.number_range(min=-1, message="Invalid id")],
        default=-1,
    )
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")
    duration_services = StringField("duration_services", [], default="")
    supplier = StringField("supplier", [], default="")
    currency = StringField("currency", [], default="MXN")
    tool = IntegerField("tool", [number_range(min=-1, max=2, message="Invalid tool")])


class ItemsPOApplicationUpdateForm(Form):
    id = IntegerField("id", [], default=-1)
    purchase_id = IntegerField("purchase_id", [], default=0)
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    brand = StringField("brand", [InputRequired()])
    category = StringField("category", [InputRequired()])
    id_inventory = IntegerField(
        "id_inventory",
        [validators.number_range(min=-1, message="Invalid id")],
        default=-1,
    )
    url = URLField("url", [], default="")
    n_parte = StringField("n_parte", [], default="")
    supplier = StringField("supplier", [], default="")
    tool = IntegerField("tool", [InputRequired()])
    comment = StringField("comment", [], default="")


class PurchaseOrderPutForm(Form):
    id = IntegerField("id", [InputRequired()])
    folio = StringField("folio", [InputRequired()])
    comment = StringField("comment", [])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    created_by = IntegerField("created_by", [])
    items = FieldList(FormField(ItemsPOUpdateForm), "items", validators=[], default=[])
    time_delivery = StringField("time_delivery", [])
    supplier = IntegerField("supplier", [InputRequired()])
    metadata_telintec = FormField(MetadataTelitencForm)
    metadata_supplier = FormField(MetadataSupplierForm)
    sm_id = IntegerField("sm_id", [], default=0)
    order_quotation = StringField("order_quotation", [], default="")


class PurchaseOrderDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])


class POAppDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )


class PurchaseOrderUpdateStatusForm(Form):
    id = IntegerField("id", [InputRequired()])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    approved = IntegerField(
        "approved", [validators.number_range(min=-1, message="Invalid id")]
    )


class POsApplicationPostForm(Form):
    reference = StringField("reference", validators=[])
    comment = StringField("comment", validators=[])
    items = FieldList(
        FormField(ItemsPOApplicationForm), "items", validators=[], default=[]
    )
    sm_id = IntegerField(
        "sm_id",
        validators=[validators.number_range(min=-1, message="Invalid id")],
        default=-1,
    )


class POsApplicationPutForm(Form):
    id = IntegerField("id", [InputRequired()])
    reference = StringField("reference", [InputRequired()])
    comment = StringField("comment", [])
    history = FieldList(FormField(HistoryPurchaseForm), "history", default=[])
    status = IntegerField(
        "status", [validators.number_range(min=-1, message="Invalid id")]
    )
    created_by = IntegerField("created_by", [])
    items = FieldList(
        FormField(ItemsPOApplicationUpdateForm), "items", validators=[], default=[]
    )


class MetadataRemissionForm(Form):
    remission_code = StringField("remission_code", [InputRequired()])
    client_id = IntegerField("client_id", [InputRequired()])
    emission = StringField("emission", [InputRequired()])
    user = StringField("user", [InputRequired()])
    planta = StringField("planta", [])
    area = StringField("area", [])
    location = StringField("location", [])
    email = StringField("email", [])
    phone = StringField("phone", [])
    observations = StringField("observations", [])
    printed = BooleanField("printed", [], default=False)
    status = IntegerField("status", [], default=0)


class ProductsPostRemissionForm(Form):
    quotation_item_id = IntegerField("quotation_item_id", [], default=0)
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    udm = StringField("udm", [InputRequired()])
    price_unit = FloatField("price_unit", [InputRequired()])


class ProductsPutRemissionForm(Form):
    id = IntegerField(
        "id", [number_range(min=-1, max=2, message="Invalid id")], default=-1
    )
    quotation_item_id = IntegerField("quotation_item_id", [], default=0)
    description = StringField("description", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    udm = StringField("udm", [InputRequired()])
    price_unit = FloatField("price_unit", [InputRequired()])


class ProductsDeleteRemissionForm(Form):
    id = IntegerField("id", [InputRequired()])


class RemissionInsertForm(Form):
    metadata = FormField(MetadataRemissionForm, "metadata")
    contract_id = IntegerField("contract_id", [], default=0)
    products = FieldList(FormField(ProductsPostRemissionForm, "products"))


class RemissionUpdateForm(Form):
    id = IntegerField("id", [InputRequired()])
    contract_id = IntegerField("contract_id", [], default=0)
    metadata = FormField(MetadataRemissionForm, "metadata")
    items = FieldList(FormField(ProductsPutRemissionForm, "items"))
    items_to_delete = FieldList(
        FormField(ProductsDeleteRemissionForm, "items_to_delete")
    )
    history = FieldList(FormField(Form), "history", default=[])


class RemissionDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])

class QuotationInsertItemForm(Form):
    report_id = IntegerField("report_id", [], default=0)
    description = StringField("description", [InputRequired()])
    udm = StringField("udm", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    item_contract_id = IntegerField("item_contract_id", [], default=0)

class QuotationUpsertItemForm(Form):
    id = IntegerField("id", validators=[number_range(min=-1, message="Invalid id")], default=-1)
    report_id = IntegerField("report_id", [], default=0)
    description = StringField("description", [InputRequired()])
    udm = StringField("udm", [InputRequired()])
    quantity = FloatField("quantity", [InputRequired()])
    unit_price = FloatField("unit_price", [InputRequired()])
    item_contract_id = IntegerField("item_contract_id", [], default=0)
    is_erased = BooleanField("is_erased", [], default=False)

class QuotationActivityCreateForm(Form):
    date_activity = StringField("date_activity", [InputRequired()])
    folio = StringField("folio", [InputRequired()])
    client_id = IntegerField("client_id", [InputRequired()])
    client_company_name = StringField("client_company_name", [InputRequired()])
    client_contact_name = StringField("client_contact_name", [InputRequired()])
    client_phone = StringField("client_phone", [InputRequired()])
    client_email = StringField("client_email", [InputRequired()])
    plant = StringField("plant", [InputRequired()])
    area = StringField("area", [InputRequired()])
    location = StringField("location", [InputRequired()])
    general_description = StringField("general_description", [InputRequired()])
    comments = StringField("comments", [InputRequired()])
    items = FieldList(FormField(QuotationUpsertItemForm), "items", validators=[], default=[])
    status = IntegerField("status", [InputRequired()], default=0)

class QuotationActivityUpdateForm(Form):
    id = IntegerField("id", [InputRequired()])
    date_activity = StringField("date_activity", [InputRequired()])
    folio = StringField("folio", [InputRequired()])
    client_id = IntegerField("client_id", [InputRequired()])
    client_company_name = StringField("client_company_name", [InputRequired()])
    client_contact_name = StringField("client_contact_name", [InputRequired()])
    client_phone = StringField("client_phone", [InputRequired()])
    client_email = StringField("client_email", [InputRequired()])
    plant = StringField("plant", [InputRequired()])
    area = StringField("area", [InputRequired()])
    location = StringField("location", [InputRequired()])
    general_description = StringField("general_description", [InputRequired()])
    comments = StringField("comments", [InputRequired()])
    items = FieldList(FormField(QuotationUpsertItemForm), "items", validators=[], default=[])
    status = IntegerField("status", [InputRequired()], default=0)

class QuotationActivityDeleteForm(Form):
    id = IntegerField("id", [InputRequired()])
    status = IntegerField("status", [InputRequired()], default=-1)

class QuotationActivityStatusUpdateForm(Form):
    id = IntegerField("id", [InputRequired()])
    status = IntegerField("status", [InputRequired()], default=-1)