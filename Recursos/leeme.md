Instrucciones para ejecutar el proyecto:

1. Abre la carpeta del "código" en tu editor de código preferido.

2. Crear un entorno virtual de ejecución, puedes hacerlo colocando "py -m venv entornoproyecto" en la consola, esto permitirá instalar las dependencias fuera de tu instalación global de python.

3. Activa tu entorno virtual, puedes hacerlo escribiendo "entornoproyecto\Scripts\activate" en la consola.

4. Instalar flet y MySQL connector, puedes hacerlo ejecutando "pip install flet" y "pip install mysql-connector-python"

5. Ahora crea la base de datos, dependiendo de tu gestor de base de datos este proceso puede variar un poco, en este ejemplo se utilizará MySQL Workbench. Abre Workbench y abre la conexión con tu base de datos. Ahora abre "homedepot sql" con un lector de notas, copia todo su contenido y pegalo en workbench, selecciona todas las lineas y ejecutalas. 

6. Ahora puedes ejecutar "main.py" y correr el programa.