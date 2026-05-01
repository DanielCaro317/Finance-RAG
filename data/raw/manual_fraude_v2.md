# Manual de Detección de Fraude Tecnológico — v2 (vigencia 2024)

## 1. Introducción
Este manual establece los lineamientos corporativos para la detección,
prevención y reporte de fraudes tecnológicos en transacciones financieras.
Aplica a Colombia y México (CO/MX) y reemplaza la versión v1 publicada en 2022.

## 2. Definiciones
- **Fraude tecnológico:** uso indebido de canales digitales (banca móvil,
  web, APIs) para obtener un beneficio económico ilícito.
- **Transacción inusual:** aquella que se desvía significativamente del
  patrón histórico del cliente.

## 3. Política de Transferencias Internacionales
- El monto máximo permitido para una transferencia internacional **sin
  aprobación adicional** es **USD 10,000**. Por encima requiere aprobación
  del oficial de cumplimiento.
- Las transferencias a jurisdicciones de alto riesgo (FATF gris/negro)
  requieren validación documental aún por debajo del umbral.

## 4. Señales de Fraude en Tarjetas
Las siguientes señales, en conjunto, elevan el score de riesgo:
1. **Velocidad anormal**: más de 5 transacciones en menos de 10 minutos.
2. **Geolocalización inusual**: transacciones en países donde el cliente
   nunca ha operado.
3. **Montos atípicos**: monto > 3 desviaciones estándar del histórico.
4. **Hora atípica**: actividad entre 02:00 y 05:00 hora local.

## 5. Procedimiento de Bloqueo
Cuando el score de riesgo > 85:
1. Bloquear la transacción de forma preventiva.
2. Notificar al cliente vía SMS y push.
3. Crear un caso en el sistema de fraudes con prioridad ALTA.
4. El analista tiene **30 minutos** para validar o liberar el bloqueo.

## 6. Reporte Regulatorio
Todo intento de fraude confirmado debe reportarse a la UIAF (CO) o UIF (MX)
dentro de los **10 días hábiles** siguientes a la confirmación.
