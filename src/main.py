import flet as ft
import mysql.connector
from decimal import Decimal, InvalidOperation

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "pruebas4s"
DB_NAME = "homedepot"

def conectar_db():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error al conectar a la DB: {err}")
        return None

def mostrar_mensaje(page: ft.Page, mensaje: str, color: str = ft.colors.RED):
    snackbar = ft.SnackBar(
        content=ft.Text(mensaje),
        bgcolor=color
    )
    page.overlay.append(snackbar)
    snackbar.open = True
    page.update()

def limpiar_campos(campos):
    for campo in campos:
        if isinstance(campo, ft.TextField):
            campo.value = ""
        elif isinstance(campo, ft.Dropdown):
             campo.value = None

def crud_articulos(page, interfaz_principal):
    page.clean()
    page.title = "Gestión de Artículos"

    txt_id_articulo = ft.TextField(label="ID Artículo", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_nombre = ft.TextField(label="Nombre", width=250)
    txt_precio = ft.TextField(label="Precio", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]", replacement_string=""))
    txt_existencias = ft.TextField(label="Existencias", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_codigo_bar = ft.TextField(label="Código Barras (13 dígitos)", width=200, max_length=13, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_unidad = ft.TextField(label="Unidad", width=150)

    campos_articulo = [txt_id_articulo, txt_nombre, txt_precio, txt_existencias, txt_codigo_bar, txt_unidad]
    id_articulo_editar = ft.Text("", visible=False)

    dt_articulos = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Precio")),
            ft.DataColumn(ft.Text("Existencias")),
            ft.DataColumn(ft.Text("Cod. Barras")),
            ft.DataColumn(ft.Text("Unidad")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        width=1000
    )

    def mostrar_articulos():
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id_articulo, Nombre, precio, existencias, codigo_bar, unidad FROM articulos ORDER BY id_articulo")
            rows = cursor.fetchall()
            dt_articulos.rows.clear()
            for row in rows:
                dt_articulos.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row[0]))),
                            ft.DataCell(ft.Text(row[1])),
                            ft.DataCell(ft.Text(f"{row[2]:.2f}")),
                            ft.DataCell(ft.Text(str(row[3]))),
                            ft.DataCell(ft.Text(row[4])),
                            ft.DataCell(ft.Text(row[5])),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.icons.EDIT, tooltip="Editar", on_click=lambda e, id=row[0]: preparar_edicion(id)),
                                ft.IconButton(ft.icons.DELETE, tooltip="Eliminar", on_click=lambda e, id=row[0]: eliminar_articulo(id), icon_color=ft.colors.RED)
                            ])),
                        ]
                    )
                )
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al leer artículos: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def agregar_articulo(e):
        if not all([txt_id_articulo.value, txt_nombre.value, txt_precio.value, txt_existencias.value, txt_codigo_bar.value, txt_unidad.value]):
            mostrar_mensaje(page, "Todos los campos son requeridos.")
            return
        if len(txt_codigo_bar.value) != 13:
             mostrar_mensaje(page, "El código de barras debe tener 13 dígitos.")
             return
        try:
            precio = Decimal(txt_precio.value)
            existencias = int(txt_existencias.value)
            id_articulo = int(txt_id_articulo.value)
        except (InvalidOperation, ValueError):
            mostrar_mensaje(page, "Precio, Existencias e ID deben ser números válidos.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = """
        INSERT INTO articulos (id_articulo, Nombre, precio, existencias, codigo_bar, unidad)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        valores = (id_articulo, txt_nombre.value, precio, existencias, txt_codigo_bar.value, txt_unidad.value)
        try:
            cursor.execute(sql, valores)
            conn.commit()
            mostrar_mensaje(page, "✅ Artículo agregado exitosamente.", "green")
            limpiar_campos(campos_articulo)
            mostrar_articulos()
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:
                 mostrar_mensaje(page, f"Error: El ID de artículo '{id_articulo}' ya existe.")
            else:
                 mostrar_mensaje(page, f"Error al agregar artículo: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def preparar_edicion(id_articulo_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Nombre, precio, existencias, codigo_bar, unidad FROM articulos WHERE id_articulo = %s", (id_articulo_sel,))
            articulo = cursor.fetchone()
            if articulo:
                txt_id_articulo.value = str(id_articulo_sel)
                txt_id_articulo.disabled = True
                id_articulo_editar.value = str(id_articulo_sel)
                txt_nombre.value = articulo[0]
                txt_precio.value = f"{articulo[1]:.2f}"
                txt_existencias.value = str(articulo[2])
                txt_codigo_bar.value = articulo[3]
                txt_unidad.value = articulo[4]
                btn_agregar.visible = False
                btn_actualizar.visible = True
                btn_cancelar_edicion.visible = True
                page.update()
            else:
                mostrar_mensaje(page, f"Artículo con ID {id_articulo_sel} no encontrado.")
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al cargar artículo para editar: {err}")
        finally:
            cursor.close()
            conn.close()

    def cancelar_edicion(e):
        limpiar_campos(campos_articulo)
        txt_id_articulo.disabled = False
        id_articulo_editar.value = ""
        btn_agregar.visible = True
        btn_actualizar.visible = False
        btn_cancelar_edicion.visible = False
        page.update()

    def actualizar_articulo(e):
        id_actual = id_articulo_editar.value
        if not id_actual:
            mostrar_mensaje(page, "No hay artículo seleccionado para actualizar.")
            return

        if not all([txt_nombre.value, txt_precio.value, txt_existencias.value, txt_codigo_bar.value, txt_unidad.value]):
            mostrar_mensaje(page, "Todos los campos (excepto ID) son requeridos.")
            return
        if len(txt_codigo_bar.value) != 13:
             mostrar_mensaje(page, "El código de barras debe tener 13 dígitos.")
             return
        try:
            precio = Decimal(txt_precio.value)
            existencias = int(txt_existencias.value)
        except (InvalidOperation, ValueError):
            mostrar_mensaje(page, "Precio y Existencias deben ser números válidos.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = """
        UPDATE articulos
        SET Nombre = %s, precio = %s, existencias = %s, codigo_bar = %s, unidad = %s
        WHERE id_articulo = %s
        """
        valores = (txt_nombre.value, precio, existencias, txt_codigo_bar.value, txt_unidad.value, int(id_actual))
        try:
            cursor.execute(sql, valores)
            conn.commit()
            if cursor.rowcount > 0:
                 mostrar_mensaje(page, "✅ Artículo actualizado exitosamente.", "green")
            else:
                 mostrar_mensaje(page, "ℹ️ No se realizaron cambios (datos iguales o ID no encontrado).", "orange")
            cancelar_edicion(None)
            mostrar_articulos()
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al actualizar artículo: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def eliminar_articulo(id_articulo_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT 1 FROM detalleventa WHERE id_articulo = %s LIMIT 1", (id_articulo_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar el artículo {id_articulo_sel} porque está referenciado en 'detalleventa'.")
                return
            cursor.execute("SELECT 1 FROM compras WHERE id_articulo = %s LIMIT 1", (id_articulo_sel,))
            if cursor.fetchone():
                 mostrar_mensaje(page, f"Error: No se puede eliminar el artículo {id_articulo_sel} porque está referenciado en 'compras'.")
                 return

            cursor.execute("DELETE FROM articulos WHERE id_articulo = %s", (id_articulo_sel,))
            conn.commit()
            if cursor.rowcount > 0:
                 mostrar_mensaje(page, f"✅ Artículo {id_articulo_sel} eliminado exitosamente.", "green")
                 mostrar_articulos()
            else:
                 mostrar_mensaje(page, f"ℹ️ Artículo {id_articulo_sel} no encontrado para eliminar.", "orange")
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al eliminar artículo {id_articulo_sel}: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    btn_agregar = ft.ElevatedButton("Agregar Artículo", on_click=agregar_articulo, icon=ft.icons.ADD)
    btn_actualizar = ft.ElevatedButton("Guardar Cambios", on_click=actualizar_articulo, icon=ft.icons.SAVE, visible=False)
    btn_cancelar_edicion = ft.ElevatedButton("Cancelar Edición", on_click=cancelar_edicion, icon=ft.icons.CANCEL, visible=False)
    btn_volver = ft.ElevatedButton("Volver al Menú", on_click=lambda e: interfaz_principal(page), icon=ft.icons.ARROW_BACK)

    page.add(
        ft.Column(
            [
                ft.Row([btn_volver], alignment=ft.MainAxisAlignment.START),
                ft.Text("Gestión de Artículos", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        txt_id_articulo,
                        txt_nombre,
                        txt_precio,
                    ], alignment=ft.MainAxisAlignment.CENTER
                ),
                 ft.Row(
                    [
                        txt_existencias,
                        txt_codigo_bar,
                        txt_unidad,
                    ], alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [btn_agregar, btn_actualizar, btn_cancelar_edicion],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Text("Artículos Existentes", size=18),
                ft.Container(
                    content=dt_articulos,
                    expand=True,
                )
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    )
    mostrar_articulos()
    page.update()

def crud_cajas(page, interfaz_principal):
    page.clean()
    page.title = "Gestión de Cajas"

    txt_id_caja = ft.TextField(label="ID Caja", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    dd_tipo_pago = ft.Dropdown(
        label="Tipo de Pago Aceptado",
        width=200,
        options=[
            ft.dropdown.Option("Efectivo"),
            ft.dropdown.Option("Tarjeta"),
            ft.dropdown.Option("Ambos"),
        ],
    )
    txt_saldo_corte = ft.TextField(label="Saldo al Corte", width=200, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]", replacement_string=""))

    campos_caja = [txt_id_caja, dd_tipo_pago, txt_saldo_corte]
    id_caja_editar = ft.Text("", visible=False)

    dt_cajas = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID Caja")),
            ft.DataColumn(ft.Text("Tipo Pago Aceptado")),
            ft.DataColumn(ft.Text("Saldo Corte")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        width=700
    )

    def mostrar_cajas():
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT idCajas, tipo_pago_aceptado, saldocorte FROM cajas ORDER BY idCajas")
            rows = cursor.fetchall()
            dt_cajas.rows.clear()
            for row in rows:
                dt_cajas.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row[0]))),
                            ft.DataCell(ft.Text(row[1])),
                            ft.DataCell(ft.Text(f"{row[2]:.2f}")),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.icons.EDIT, tooltip="Editar", on_click=lambda e, id=row[0]: preparar_edicion_caja(id)),
                                ft.IconButton(ft.icons.DELETE, tooltip="Eliminar", on_click=lambda e, id=row[0]: eliminar_caja(id), icon_color=ft.colors.RED)
                            ])),
                        ]
                    )
                )
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al leer cajas: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def agregar_caja(e):
        if not all([txt_id_caja.value, dd_tipo_pago.value, txt_saldo_corte.value]):
            mostrar_mensaje(page, "Todos los campos son requeridos.")
            return
        try:
            saldo = Decimal(txt_saldo_corte.value)
            id_caja = int(txt_id_caja.value)
        except (InvalidOperation, ValueError):
            mostrar_mensaje(page, "Saldo e ID deben ser números válidos.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "INSERT INTO cajas (idCajas, tipo_pago_aceptado, saldocorte) VALUES (%s, %s, %s)"
        valores = (id_caja, dd_tipo_pago.value, saldo)
        try:
            cursor.execute(sql, valores)
            conn.commit()
            mostrar_mensaje(page, "✅ Caja agregada exitosamente.", "green")
            limpiar_campos(campos_caja)
            mostrar_cajas()
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:
                mostrar_mensaje(page, f"Error: El ID de caja '{id_caja}' ya existe.")
            else:
                mostrar_mensaje(page, f"Error al agregar caja: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def preparar_edicion_caja(id_caja_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tipo_pago_aceptado, saldocorte FROM cajas WHERE idCajas = %s", (id_caja_sel,))
            caja = cursor.fetchone()
            if caja:
                txt_id_caja.value = str(id_caja_sel)
                txt_id_caja.disabled = True
                id_caja_editar.value = str(id_caja_sel)
                dd_tipo_pago.value = caja[0]
                txt_saldo_corte.value = f"{caja[1]:.2f}"
                btn_agregar_caja.visible = False
                btn_actualizar_caja.visible = True
                btn_cancelar_edicion_caja.visible = True
                page.update()
            else:
                mostrar_mensaje(page, f"Caja con ID {id_caja_sel} no encontrada.")
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al cargar caja para editar: {err}")
        finally:
            cursor.close()
            conn.close()

    def cancelar_edicion_caja(e):
        limpiar_campos(campos_caja)
        txt_id_caja.disabled = False
        id_caja_editar.value = ""
        btn_agregar_caja.visible = True
        btn_actualizar_caja.visible = False
        btn_cancelar_edicion_caja.visible = False
        page.update()

    def actualizar_caja(e):
        id_actual = id_caja_editar.value
        if not id_actual:
            mostrar_mensaje(page, "No hay caja seleccionada para actualizar.")
            return
        if not all([dd_tipo_pago.value, txt_saldo_corte.value]):
            mostrar_mensaje(page, "Tipo de pago y saldo son requeridos.")
            return
        try:
            saldo = Decimal(txt_saldo_corte.value)
        except InvalidOperation:
            mostrar_mensaje(page, "Saldo debe ser un número válido.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "UPDATE cajas SET tipo_pago_aceptado = %s, saldocorte = %s WHERE idCajas = %s"
        valores = (dd_tipo_pago.value, saldo, int(id_actual))
        try:
            cursor.execute(sql, valores)
            conn.commit()
            if cursor.rowcount > 0:
                mostrar_mensaje(page, "✅ Caja actualizada exitosamente.", "green")
            else:
                mostrar_mensaje(page, "ℹ️ No se realizaron cambios.", "orange")
            cancelar_edicion_caja(None)
            mostrar_cajas()
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al actualizar caja: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def eliminar_caja(id_caja_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
             cursor.execute("SELECT 1 FROM usocajas WHERE idCajas = %s LIMIT 1", (id_caja_sel,))
             if cursor.fetchone():
                  mostrar_mensaje(page, f"Error: No se puede eliminar la caja {id_caja_sel} porque está referenciada en 'usocajas'.")
                  return

             cursor.execute("DELETE FROM cajas WHERE idCajas = %s", (id_caja_sel,))
             conn.commit()
             if cursor.rowcount > 0:
                  mostrar_mensaje(page, f"✅ Caja {id_caja_sel} eliminada exitosamente.", "green")
                  mostrar_cajas()
             else:
                  mostrar_mensaje(page, f"ℹ️ Caja {id_caja_sel} no encontrada.", "orange")
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al eliminar caja {id_caja_sel}: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    btn_agregar_caja = ft.ElevatedButton("Agregar Caja", on_click=agregar_caja, icon=ft.icons.ADD)
    btn_actualizar_caja = ft.ElevatedButton("Guardar Cambios", on_click=actualizar_caja, icon=ft.icons.SAVE, visible=False)
    btn_cancelar_edicion_caja = ft.ElevatedButton("Cancelar Edición", on_click=cancelar_edicion_caja, icon=ft.icons.CANCEL, visible=False)
    btn_volver_caja = ft.ElevatedButton("Volver al Menú", on_click=lambda e: interfaz_principal(page), icon=ft.icons.ARROW_BACK)

    page.add(
        ft.Column(
            [
                ft.Row([btn_volver_caja], alignment=ft.MainAxisAlignment.START),
                ft.Text("Gestión de Cajas", size=24, weight=ft.FontWeight.BOLD),
                ft.Row(
                    [
                        txt_id_caja,
                        dd_tipo_pago,
                        txt_saldo_corte,
                    ], alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [btn_agregar_caja, btn_actualizar_caja, btn_cancelar_edicion_caja],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Text("Cajas Existentes", size=18),
                 ft.Container(
                    content=dt_cajas,
                    expand=True,
                )
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    )
    mostrar_cajas()
    page.update()

def crud_empleados(page, interfaz_principal):
    page.clean()
    page.title = "Gestión de Empleados"

    txt_id_empleado = ft.TextField(label="ID Empleado", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_nombre_emp = ft.TextField(label="Nombre", width=200)
    txt_apellidos_emp = ft.TextField(label="Apellidos", width=250)
    txt_sueldo = ft.TextField(label="Sueldo", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9.]", replacement_string=""))
    txt_puesto = ft.TextField(label="Puesto", width=200)

    campos_empleado = [txt_id_empleado, txt_nombre_emp, txt_apellidos_emp, txt_sueldo, txt_puesto]
    id_empleado_editar = ft.Text("", visible=False)

    dt_empleados = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre")),
            ft.DataColumn(ft.Text("Apellidos")),
            ft.DataColumn(ft.Text("Sueldo")),
            ft.DataColumn(ft.Text("Puesto")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        width=900
    )

    def mostrar_empleados():
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT idEmpleado, nombre, apellidos, sueldo, puesto FROM empleados ORDER BY idEmpleado")
            rows = cursor.fetchall()
            dt_empleados.rows.clear()
            for row in rows:
                dt_empleados.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row[0]))),
                            ft.DataCell(ft.Text(row[1])),
                            ft.DataCell(ft.Text(row[2])),
                            ft.DataCell(ft.Text(f"{row[3]:.2f}")),
                            ft.DataCell(ft.Text(row[4])),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.icons.EDIT, tooltip="Editar", on_click=lambda e, id=row[0]: preparar_edicion_emp(id)),
                                ft.IconButton(ft.icons.DELETE, tooltip="Eliminar", on_click=lambda e, id=row[0]: eliminar_empleado(id), icon_color=ft.colors.RED)
                            ])),
                        ]
                    )
                )
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al leer empleados: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def agregar_empleado(e):
        if not all([txt_id_empleado.value, txt_nombre_emp.value, txt_apellidos_emp.value, txt_sueldo.value, txt_puesto.value]):
            mostrar_mensaje(page, "Todos los campos son requeridos.")
            return
        try:
            sueldo = Decimal(txt_sueldo.value)
            id_empleado = int(txt_id_empleado.value)
        except (InvalidOperation, ValueError):
            mostrar_mensaje(page, "Sueldo e ID deben ser números válidos.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "INSERT INTO empleados (idEmpleado, nombre, apellidos, sueldo, puesto) VALUES (%s, %s, %s, %s, %s)"
        valores = (id_empleado, txt_nombre_emp.value, txt_apellidos_emp.value, sueldo, txt_puesto.value)
        try:
            cursor.execute(sql, valores)
            conn.commit()
            mostrar_mensaje(page, "✅ Empleado agregado exitosamente.", "green")
            limpiar_campos(campos_empleado)
            mostrar_empleados()
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:
                mostrar_mensaje(page, f"Error: El ID de empleado '{id_empleado}' ya existe.")
            else:
                mostrar_mensaje(page, f"Error al agregar empleado: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def preparar_edicion_emp(id_emp_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT nombre, apellidos, sueldo, puesto FROM empleados WHERE idEmpleado = %s", (id_emp_sel,))
            empleado = cursor.fetchone()
            if empleado:
                txt_id_empleado.value = str(id_emp_sel)
                txt_id_empleado.disabled = True
                id_empleado_editar.value = str(id_emp_sel)
                txt_nombre_emp.value = empleado[0]
                txt_apellidos_emp.value = empleado[1]
                txt_sueldo.value = f"{empleado[2]:.2f}"
                txt_puesto.value = empleado[3]
                btn_agregar_emp.visible = False
                btn_actualizar_emp.visible = True
                btn_cancelar_edicion_emp.visible = True
                page.update()
            else:
                 mostrar_mensaje(page, f"Empleado con ID {id_emp_sel} no encontrado.")
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al cargar empleado para editar: {err}")
        finally:
            cursor.close()
            conn.close()

    def cancelar_edicion_emp(e):
        limpiar_campos(campos_empleado)
        txt_id_empleado.disabled = False
        id_empleado_editar.value = ""
        btn_agregar_emp.visible = True
        btn_actualizar_emp.visible = False
        btn_cancelar_edicion_emp.visible = False
        page.update()

    def actualizar_empleado(e):
        id_actual = id_empleado_editar.value
        if not id_actual:
            mostrar_mensaje(page, "No hay empleado seleccionado para actualizar.")
            return
        if not all([txt_nombre_emp.value, txt_apellidos_emp.value, txt_sueldo.value, txt_puesto.value]):
            mostrar_mensaje(page, "Nombre, apellidos, sueldo y puesto son requeridos.")
            return
        try:
            sueldo = Decimal(txt_sueldo.value)
        except InvalidOperation:
            mostrar_mensaje(page, "Sueldo debe ser un número válido.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "UPDATE empleados SET nombre = %s, apellidos = %s, sueldo = %s, puesto = %s WHERE idEmpleado = %s"
        valores = (txt_nombre_emp.value, txt_apellidos_emp.value, sueldo, txt_puesto.value, int(id_actual))
        try:
            cursor.execute(sql, valores)
            conn.commit()
            if cursor.rowcount > 0:
                mostrar_mensaje(page, "✅ Empleado actualizado exitosamente.", "green")
            else:
                mostrar_mensaje(page, "ℹ️ No se realizaron cambios.", "orange")
            cancelar_edicion_emp(None)
            mostrar_empleados()
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al actualizar empleado: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def eliminar_empleado(id_emp_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM ventas WHERE idEmpleado = %s LIMIT 1", (id_emp_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar empleado {id_emp_sel} (referenciado en 'ventas').")
                return
            cursor.execute("SELECT 1 FROM cambiosydevoluciones WHERE idEmpleado = %s LIMIT 1", (id_emp_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar empleado {id_emp_sel} (referenciado en 'cambiosydevoluciones').")
                return
            cursor.execute("SELECT 1 FROM usocajas WHERE idEmpleado = %s LIMIT 1", (id_emp_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar empleado {id_emp_sel} (referenciado en 'usocajas').")
                return

            cursor.execute("DELETE FROM empleados WHERE idEmpleado = %s", (id_emp_sel,))
            conn.commit()
            if cursor.rowcount > 0:
                 mostrar_mensaje(page, f"✅ Empleado {id_emp_sel} eliminado exitosamente.", "green")
                 mostrar_empleados()
            else:
                 mostrar_mensaje(page, f"ℹ️ Empleado {id_emp_sel} no encontrado.", "orange")
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al eliminar empleado {id_emp_sel}: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    btn_agregar_emp = ft.ElevatedButton("Agregar Empleado", on_click=agregar_empleado, icon=ft.icons.ADD)
    btn_actualizar_emp = ft.ElevatedButton("Guardar Cambios", on_click=actualizar_empleado, icon=ft.icons.SAVE, visible=False)
    btn_cancelar_edicion_emp = ft.ElevatedButton("Cancelar Edición", on_click=cancelar_edicion_emp, icon=ft.icons.CANCEL, visible=False)
    btn_volver_emp = ft.ElevatedButton("Volver al Menú", on_click=lambda e: interfaz_principal(page), icon=ft.icons.ARROW_BACK)

    page.add(
        ft.Column(
            [
                ft.Row([btn_volver_emp], alignment=ft.MainAxisAlignment.START),
                ft.Text("Gestión de Empleados", size=24, weight=ft.FontWeight.BOLD),
                 ft.Row(
                    [txt_id_empleado, txt_nombre_emp, txt_apellidos_emp],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [txt_sueldo, txt_puesto],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [btn_agregar_emp, btn_actualizar_emp, btn_cancelar_edicion_emp],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Text("Empleados Existentes", size=18),
                 ft.Container(content=dt_empleados, expand=True)
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    )
    mostrar_empleados()
    page.update()

def crud_clientes(page, interfaz_principal):
    page.clean()
    page.title = "Gestión de Clientes"

    txt_id_cliente = ft.TextField(label="ID Cliente", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_nombre1_cli = ft.TextField(label="Primer Nombre", width=200)
    txt_nombre2_cli = ft.TextField(label="Segundo Nombre (Opcional)", width=200)
    txt_apellidos_cli = ft.TextField(label="Apellidos", width=250)
    txt_calle_num = ft.TextField(label="Calle y Número", width=300)
    txt_telefono = ft.TextField(label="Teléfono (10 dígitos)", width=150, max_length=10, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_cp = ft.TextField(label="Código Postal", width=100, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_ciudad = ft.TextField(label="Ciudad", width=200)

    campos_cliente = [txt_id_cliente, txt_nombre1_cli, txt_nombre2_cli, txt_apellidos_cli, txt_calle_num, txt_telefono, txt_cp, txt_ciudad]
    id_cliente_editar = ft.Text("", visible=False)

    dt_clientes = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre Completo")),
            ft.DataColumn(ft.Text("Dirección")),
            ft.DataColumn(ft.Text("Teléfono")),
            ft.DataColumn(ft.Text("CP")),
            ft.DataColumn(ft.Text("Ciudad")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        width=1200
    )

    def mostrar_clientes():
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id_Cliente,
                       CONCAT_WS(' ', nombre_1, nombre_2, apellidos) AS nombre_completo,
                       calle_ynum, telefono, codigo_postal, ciudad
                FROM clientes ORDER BY id_Cliente
            """)
            rows = cursor.fetchall()
            dt_clientes.rows.clear()
            for row in rows:
                dt_clientes.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row[0]))),
                            ft.DataCell(ft.Text(row[1])),
                            ft.DataCell(ft.Text(row[2])),
                            ft.DataCell(ft.Text(row[3])),
                            ft.DataCell(ft.Text(row[4])),
                            ft.DataCell(ft.Text(row[5] or "")),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.icons.EDIT, tooltip="Editar", on_click=lambda e, id=row[0]: preparar_edicion_cli(id)),
                                ft.IconButton(ft.icons.DELETE, tooltip="Eliminar", on_click=lambda e, id=row[0]: eliminar_cliente(id), icon_color=ft.colors.RED)
                            ])),
                        ]
                    )
                )
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al leer clientes: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def agregar_cliente(e):
        if not all([txt_id_cliente.value, txt_nombre1_cli.value, txt_apellidos_cli.value, txt_calle_num.value, txt_telefono.value, txt_cp.value]):
              mostrar_mensaje(page, "ID, Nombre 1, Apellidos, Calle/Núm, Teléfono y CP son requeridos.")
              return
        if len(txt_telefono.value) != 10:
              mostrar_mensaje(page, "El teléfono debe tener 10 dígitos.")
              return
        try:
            id_cliente = int(txt_id_cliente.value)
        except ValueError:
            mostrar_mensaje(page, "ID Cliente debe ser un número válido.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = """
        INSERT INTO clientes (id_Cliente, nombre_1, nombre_2, apellidos, calle_ynum, telefono, codigo_postal, ciudad)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        nombre2 = txt_nombre2_cli.value if txt_nombre2_cli.value else None
        ciudad = txt_ciudad.value if txt_ciudad.value else None
        valores = (id_cliente, txt_nombre1_cli.value, nombre2, txt_apellidos_cli.value, txt_calle_num.value, txt_telefono.value, txt_cp.value, ciudad)

        try:
            cursor.execute(sql, valores)
            conn.commit()
            mostrar_mensaje(page, "✅ Cliente agregado exitosamente.", "green")
            limpiar_campos(campos_cliente)
            mostrar_clientes()
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:
                mostrar_mensaje(page, f"Error: El ID de cliente '{id_cliente}' ya existe.")
            else:
                mostrar_mensaje(page, f"Error al agregar cliente: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def preparar_edicion_cli(id_cli_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT nombre_1, nombre_2, apellidos, calle_ynum, telefono, codigo_postal, ciudad FROM clientes WHERE id_Cliente = %s", (id_cli_sel,))
            cliente = cursor.fetchone()
            if cliente:
                txt_id_cliente.value = str(id_cli_sel)
                txt_id_cliente.disabled = True
                id_cliente_editar.value = str(id_cli_sel)
                txt_nombre1_cli.value = cliente[0]
                txt_nombre2_cli.value = cliente[1] or ""
                txt_apellidos_cli.value = cliente[2]
                txt_calle_num.value = cliente[3]
                txt_telefono.value = cliente[4]
                txt_cp.value = cliente[5]
                txt_ciudad.value = cliente[6] or ""
                btn_agregar_cli.visible = False
                btn_actualizar_cli.visible = True
                btn_cancelar_edicion_cli.visible = True
                page.update()
            else:
                 mostrar_mensaje(page, f"Cliente con ID {id_cli_sel} no encontrado.")
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al cargar cliente para editar: {err}")
        finally:
            cursor.close()
            conn.close()

    def cancelar_edicion_cli(e):
        limpiar_campos(campos_cliente)
        txt_id_cliente.disabled = False
        id_cliente_editar.value = ""
        btn_agregar_cli.visible = True
        btn_actualizar_cli.visible = False
        btn_cancelar_edicion_cli.visible = False
        page.update()

    def actualizar_cliente(e):
        id_actual = id_cliente_editar.value
        if not id_actual:
            mostrar_mensaje(page, "No hay cliente seleccionado para actualizar.")
            return
        if not all([txt_nombre1_cli.value, txt_apellidos_cli.value, txt_calle_num.value, txt_telefono.value, txt_cp.value]):
              mostrar_mensaje(page, "Nombre 1, Apellidos, Calle/Núm, Teléfono y CP son requeridos.")
              return
        if len(txt_telefono.value) != 10:
              mostrar_mensaje(page, "El teléfono debe tener 10 dígitos.")
              return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = """
        UPDATE clientes
        SET nombre_1 = %s, nombre_2 = %s, apellidos = %s, calle_ynum = %s,
            telefono = %s, codigo_postal = %s, ciudad = %s
        WHERE id_Cliente = %s
        """
        nombre2 = txt_nombre2_cli.value if txt_nombre2_cli.value else None
        ciudad = txt_ciudad.value if txt_ciudad.value else None
        valores = (txt_nombre1_cli.value, nombre2, txt_apellidos_cli.value, txt_calle_num.value, txt_telefono.value, txt_cp.value, ciudad, int(id_actual))

        try:
            cursor.execute(sql, valores)
            conn.commit()
            if cursor.rowcount > 0:
                mostrar_mensaje(page, "✅ Cliente actualizado exitosamente.", "green")
            else:
                mostrar_mensaje(page, "ℹ️ No se realizaron cambios.", "orange")
            cancelar_edicion_cli(None)
            mostrar_clientes()
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al actualizar cliente: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def eliminar_cliente(id_cli_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM ventas WHERE id_Cliente = %s LIMIT 1", (id_cli_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar cliente {id_cli_sel} (referenciado en 'ventas').")
                return

            cursor.execute("DELETE FROM clientes WHERE id_Cliente = %s", (id_cli_sel,))
            conn.commit()
            if cursor.rowcount > 0:
                 mostrar_mensaje(page, f"✅ Cliente {id_cli_sel} eliminado exitosamente.", "green")
                 mostrar_clientes()
            else:
                 mostrar_mensaje(page, f"ℹ️ Cliente {id_cli_sel} no encontrado.", "orange")
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al eliminar cliente {id_cli_sel}: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    btn_agregar_cli = ft.ElevatedButton("Agregar Cliente", on_click=agregar_cliente, icon=ft.icons.ADD)
    btn_actualizar_cli = ft.ElevatedButton("Guardar Cambios", on_click=actualizar_cliente, icon=ft.icons.SAVE, visible=False)
    btn_cancelar_edicion_cli = ft.ElevatedButton("Cancelar Edición", on_click=cancelar_edicion_cli, icon=ft.icons.CANCEL, visible=False)
    btn_volver_cli = ft.ElevatedButton("Volver al Menú", on_click=lambda e: interfaz_principal(page), icon=ft.icons.ARROW_BACK)

    page.add(
        ft.Column(
            [
                ft.Row([btn_volver_cli], alignment=ft.MainAxisAlignment.START),
                ft.Text("Gestión de Clientes", size=24, weight=ft.FontWeight.BOLD),
                 ft.Row(
                    [txt_id_cliente, txt_nombre1_cli, txt_nombre2_cli, txt_apellidos_cli],
                    alignment=ft.MainAxisAlignment.CENTER, wrap=True
                ),
                ft.Row(
                    [txt_calle_num, txt_telefono, txt_cp, txt_ciudad],
                    alignment=ft.MainAxisAlignment.CENTER, wrap=True
                ),
                ft.Row(
                    [btn_agregar_cli, btn_actualizar_cli, btn_cancelar_edicion_cli],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Text("Clientes Existentes", size=18),
                 ft.Container(content=dt_clientes, expand=True)
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    )
    mostrar_clientes()
    page.update()

def crud_proveedores(page, interfaz_principal):
    page.clean()
    page.title = "Gestión de Proveedores"

    txt_id_proveedor = ft.TextField(label="ID Proveedor", width=150, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]", replacement_string=""))
    txt_nombre_prov = ft.TextField(label="Nombre Proveedor", width=300)

    campos_proveedor = [txt_id_proveedor, txt_nombre_prov]
    id_proveedor_editar = ft.Text("", visible=False)

    dt_proveedores = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Nombre Proveedor")),
            ft.DataColumn(ft.Text("Acciones")),
        ],
        rows=[],
        width=600
    )

    def mostrar_proveedores():
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT idProveedores, Nombre_prov FROM proveedores ORDER BY idProveedores")
            rows = cursor.fetchall()
            dt_proveedores.rows.clear()
            for row in rows:
                dt_proveedores.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(row[0]))),
                            ft.DataCell(ft.Text(row[1])),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.icons.EDIT, tooltip="Editar", on_click=lambda e, id=row[0]: preparar_edicion_prov(id)),
                                ft.IconButton(ft.icons.DELETE, tooltip="Eliminar", on_click=lambda e, id=row[0]: eliminar_proveedor(id), icon_color=ft.colors.RED)
                            ])),
                        ]
                    )
                )
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al leer proveedores: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def agregar_proveedor(e):
        if not all([txt_id_proveedor.value, txt_nombre_prov.value]):
            mostrar_mensaje(page, "Ambos campos son requeridos.")
            return
        try:
            id_proveedor = int(txt_id_proveedor.value)
        except ValueError:
            mostrar_mensaje(page, "ID Proveedor debe ser un número válido.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "INSERT INTO proveedores (idProveedores, Nombre_prov) VALUES (%s, %s)"
        valores = (id_proveedor, txt_nombre_prov.value)
        try:
            cursor.execute(sql, valores)
            conn.commit()
            mostrar_mensaje(page, "✅ Proveedor agregado exitosamente.", "green")
            limpiar_campos(campos_proveedor)
            mostrar_proveedores()
        except mysql.connector.Error as err:
            conn.rollback()
            if err.errno == 1062:
                mostrar_mensaje(page, f"Error: El ID de proveedor '{id_proveedor}' ya existe.")
            else:
                mostrar_mensaje(page, f"Error al agregar proveedor: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def preparar_edicion_prov(id_prov_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT Nombre_prov FROM proveedores WHERE idProveedores = %s", (id_prov_sel,))
            proveedor = cursor.fetchone()
            if proveedor:
                txt_id_proveedor.value = str(id_prov_sel)
                txt_id_proveedor.disabled = True
                id_proveedor_editar.value = str(id_prov_sel)
                txt_nombre_prov.value = proveedor[0]
                btn_agregar_prov.visible = False
                btn_actualizar_prov.visible = True
                btn_cancelar_edicion_prov.visible = True
                page.update()
            else:
                 mostrar_mensaje(page, f"Proveedor con ID {id_prov_sel} no encontrado.")
        except mysql.connector.Error as err:
            mostrar_mensaje(page, f"Error al cargar proveedor para editar: {err}")
        finally:
            cursor.close()
            conn.close()

    def cancelar_edicion_prov(e):
        limpiar_campos(campos_proveedor)
        txt_id_proveedor.disabled = False
        id_proveedor_editar.value = ""
        btn_agregar_prov.visible = True
        btn_actualizar_prov.visible = False
        btn_cancelar_edicion_prov.visible = False
        page.update()

    def actualizar_proveedor(e):
        id_actual = id_proveedor_editar.value
        if not id_actual:
            mostrar_mensaje(page, "No hay proveedor seleccionado para actualizar.")
            return
        if not txt_nombre_prov.value:
            mostrar_mensaje(page, "El nombre del proveedor es requerido.")
            return

        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        sql = "UPDATE proveedores SET Nombre_prov = %s WHERE idProveedores = %s"
        valores = (txt_nombre_prov.value, int(id_actual))
        try:
            cursor.execute(sql, valores)
            conn.commit()
            if cursor.rowcount > 0:
                mostrar_mensaje(page, "✅ Proveedor actualizado exitosamente.", "green")
            else:
                mostrar_mensaje(page, "ℹ️ No se realizaron cambios.", "orange")
            cancelar_edicion_prov(None)
            mostrar_proveedores()
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al actualizar proveedor: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    def eliminar_proveedor(id_prov_sel):
        conn = conectar_db()
        if not conn: return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM compras WHERE idProveedores = %s LIMIT 1", (id_prov_sel,))
            if cursor.fetchone():
                mostrar_mensaje(page, f"Error: No se puede eliminar proveedor {id_prov_sel} (referenciado en 'compras').")
                return

            cursor.execute("DELETE FROM proveedores WHERE idProveedores = %s", (id_prov_sel,))
            conn.commit()
            if cursor.rowcount > 0:
                 mostrar_mensaje(page, f"✅ Proveedor {id_prov_sel} eliminado exitosamente.", "green")
                 mostrar_proveedores()
            else:
                 mostrar_mensaje(page, f"ℹ️ Proveedor {id_prov_sel} no encontrado.", "orange")
        except mysql.connector.Error as err:
            conn.rollback()
            mostrar_mensaje(page, f"Error al eliminar proveedor {id_prov_sel}: {err}")
        finally:
            cursor.close()
            conn.close()
        page.update()

    btn_agregar_prov = ft.ElevatedButton("Agregar Proveedor", on_click=agregar_proveedor, icon=ft.icons.ADD)
    btn_actualizar_prov = ft.ElevatedButton("Guardar Cambios", on_click=actualizar_proveedor, icon=ft.icons.SAVE, visible=False)
    btn_cancelar_edicion_prov = ft.ElevatedButton("Cancelar Edición", on_click=cancelar_edicion_prov, icon=ft.icons.CANCEL, visible=False)
    btn_volver_prov = ft.ElevatedButton("Volver al Menú", on_click=lambda e: interfaz_principal(page), icon=ft.icons.ARROW_BACK)

    page.add(
        ft.Column(
            [
                ft.Row([btn_volver_prov], alignment=ft.MainAxisAlignment.START),
                ft.Text("Gestión de Proveedores", size=24, weight=ft.FontWeight.BOLD),
                 ft.Row(
                    [txt_id_proveedor, txt_nombre_prov],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Row(
                    [btn_agregar_prov, btn_actualizar_prov, btn_cancelar_edicion_prov],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Divider(),
                ft.Text("Proveedores Existentes", size=18),
                 ft.Container(content=dt_proveedores, expand=True)
            ],
            scroll=ft.ScrollMode.ADAPTIVE,
            expand=True
        )
    )
    mostrar_proveedores()
    page.update()

def main(page: ft.Page):
    page.title = "Gestión Home Depot DB"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 1200
    page.window_height = 800

    def interfaz_principal(page):
        page.clean()
        page.title = "Gestión Home Depot DB - Menú Principal"
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        titulo = ft.Text("Selecciona la tabla a gestionar:", size=30, weight=ft.FontWeight.BOLD)

        btn_articulos = ft.ElevatedButton("Artículos", on_click=lambda e: crud_articulos(page, interfaz_principal), width=150, height=50, icon=ft.icons.LIST_ALT)
        btn_cajas = ft.ElevatedButton("Cajas", on_click=lambda e: crud_cajas(page, interfaz_principal), width=150, height=50, icon=ft.icons.POINT_OF_SALE)
        btn_empleados = ft.ElevatedButton("Empleados", on_click=lambda e: crud_empleados(page, interfaz_principal), width=150, height=50, icon=ft.icons.PEOPLE)
        btn_clientes = ft.ElevatedButton("Clientes", on_click=lambda e: crud_clientes(page, interfaz_principal), width=150, height=50, icon=ft.icons.ACCOUNT_CIRCLE)
        btn_proveedores = ft.ElevatedButton("Proveedores", on_click=lambda e: crud_proveedores(page, interfaz_principal), width=150, height=50, icon=ft.icons.LOCAL_SHIPPING)

        page.add(
            ft.Column(
                [
                    titulo,
                    ft.Row(
                        [btn_articulos, btn_cajas, btn_empleados],
                        alignment=ft.MainAxisAlignment.CENTER, spacing=20
                    ),
                     ft.Row(
                        [btn_clientes, btn_proveedores],
                        alignment=ft.MainAxisAlignment.CENTER, spacing=20
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=30
            )
        )
        page.update()

    interfaz_principal(page)

if __name__ == "__main__":
    conn_test = conectar_db()
    if conn_test:
        print("Conexión inicial a la base de datos exitosa.")
        conn_test.close()
        ft.app(target=main)
    else:
        print("ERROR: No se pudo conectar a la base de datos. La aplicación no se iniciará.")