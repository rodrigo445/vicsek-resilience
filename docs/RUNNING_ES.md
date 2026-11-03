# Ejecución final en Windows / VS Code

El proyecto exploratorio original se considera congelado y se usa únicamente como fuente de los datasets finales. El repositorio limpio escribe todos sus outputs en su propio `results/final/` y `figures/final/`.

No es necesario activar Conda si se llama directamente al intérprete del entorno.

## 1. Definir rutas

```powershell
$PYTHON = "C:\ruta\a\anaconda3\envs\vicsek\python.exe"
$DATA_ROOT = "C:\ruta\al\proyecto\Vicsek_Resilience"
```

## 2. Instalar el repositorio

Desde la raíz del repositorio limpio:

```powershell
& $PYTHON -m pip install -e ".[dev]"
```

## 3. Ejecutar los tests

```powershell
& $PYTHON -m pytest
```

## 4. Comprobar los inputs congelados

```powershell
& $PYTHON scripts\00_check_inputs.py --project-root $DATA_ROOT
```

La comprobación valida ruta, número de filas, tamaño en bytes y SHA-256. Si un dataset no coincide exactamente con la versión auditada, el pipeline se detiene antes del análisis.

## 5. Reproducir todo el análisis final

```powershell
& $PYTHON scripts\reproduce.py --project-root $DATA_ROOT
```

Este comando ejecuta:

1. auditoría byte a byte de los inputs canónicos;
2. análisis global para `N=100, 400, 1600`;
3. análisis local Ridge + HGB para `N=400, m=10`;
4. análisis local Ridge + HGB para `N=1600, m=10`;
5. análisis local Ridge + HGB para `N=1600, m=160`;
6. bootstrap within-state;
7. validación contra benchmarks congelados;
8. tablas finales;
9. figuras finales.

Para una comprobación más rápida puede omitirse el dataset grande `m=160`:

```powershell
& $PYTHON scripts\reproduce.py --project-root $DATA_ROOT --skip-m160
```

## Regla de validación

Los resultados robustos son gates de bloqueo. Si uno se sale de tolerancia, el pipeline termina con error antes de considerar válidas las figuras finales.

La única excepción explícita es `N=400, P0 -> P1`, conservada como auditoría de sensibilidad legacy porque la implementación histórica exacta de ese modelo inestable no quedó preservada. No se modifica el código limpio para forzar artificialmente su coincidencia.
