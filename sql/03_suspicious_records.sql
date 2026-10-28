-- 03. Suspicious records (equivalent to the error_* flags of the Python pipeline)
SELECT *
FROM dbo.pedidos_logistica
WHERE unidades_pedidas IS NULL
   OR unidades_pedidas <= 0
   OR unidades_entregadas < 0
   OR unidades_entregadas > unidades_pedidas
   OR (unidades_entregadas IS NULL AND fecha_entrega IS NOT NULL)
   OR costo_transporte IS NULL
   OR costo_transporte < 0
   OR fecha_pedido IS NULL
   OR fecha_prometida IS NULL
   OR fecha_prometida < fecha_pedido
   OR (fecha_entrega IS NOT NULL AND fecha_entrega < fecha_pedido);
