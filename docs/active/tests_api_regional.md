# Tests de API para Scrape Regional

## Resumen

Se han creado tests completos para la API de scrape regional y los endpoints de jobs, cubriendo todo el flujo desde la creación del job hasta la descarga del CSV.

## Archivos Creados

### 1. `tests_api/test_regional_scrape_api.py`

Tests completos para el endpoint `/scrape/regional`:

#### Tests de Creación de Job
- `test_create_regional_scrape_job`: Crea un job básico
- `test_create_regional_scrape_job_with_custom_csv`: Crea job con CSV personalizado
- `test_create_regional_scrape_job_with_debug`: Crea job con debug habilitado
- `test_create_regional_scrape_job_invalid_departamento`: Valida departamento inválido
- `test_create_regional_scrape_job_invalid_anio`: Valida año inválido

#### Tests de Flujo Completo
- `test_regional_scrape_full_flow`: Flujo completo (crear → status → result)
- `test_regional_scrape_download_csv`: Descarga del CSV generado
- `test_regional_scrape_job_error_handling`: Manejo de errores

#### Tests de Descarga CSV
- `test_download_csv_job_not_found`: Error cuando job no existe
- `test_download_csv_job_not_regional`: Error cuando job no es regional
- `test_download_csv_job_not_completed`: Error cuando job no está completado

### 2. `tests_api/test_jobs_api_complete.py`

Tests completos para los endpoints de jobs:

#### Tests de Status (`GET /jobs/{job_id}`)
- `test_get_job_status_success`: Obtener status exitosamente
- `test_get_job_status_not_found`: Error cuando job no existe
- `test_get_job_status_with_error`: Status incluye error si falló

#### Tests de Result (`GET /jobs/{job_id}/result`)
- `test_get_job_result_success`: Obtener resultado exitosamente
- `test_get_job_result_not_found`: Error cuando job no existe
- `test_get_job_result_regional_with_csv_path`: Resultado incluye csv_path

#### Tests de Download (`GET /jobs/{job_id}/download`)
- `test_download_csv_success`: Descarga exitosa
- `test_download_csv_not_found`: Error cuando job no existe
- `test_download_csv_wrong_job_type`: Error cuando job no es regional
- `test_download_csv_job_not_completed`: Error cuando job no está completado
- `test_download_csv_file_not_exists`: Error cuando archivo no existe

#### Tests de Cancel (`POST /jobs/{job_id}/cancel`)
- `test_cancel_job_success`: Cancelar job exitosamente
- `test_cancel_job_not_found`: Error cuando job no existe
- `test_cancel_job_already_completed`: Cancelar job ya completado

## Cobertura de Tests

### Endpoints Cubiertos

1. **POST /scrape/regional**
   - ✅ Creación exitosa
   - ✅ Validación de parámetros
   - ✅ Manejo de errores

2. **GET /jobs/{job_id}**
   - ✅ Obtener status
   - ✅ Job no encontrado
   - ✅ Status con error

3. **GET /jobs/{job_id}/result**
   - ✅ Obtener resultado
   - ✅ Job no encontrado
   - ✅ Resultado con csv_path

4. **GET /jobs/{job_id}/download**
   - ✅ Descarga exitosa
   - ✅ Validaciones (tipo, estado, existencia)
   - ✅ Manejo de errores

5. **POST /jobs/{job_id}/cancel**
   - ✅ Cancelar job
   - ✅ Validaciones

### Flujos Completos Testeados

1. **Flujo Completo de Scrape Regional:**
   ```
   POST /scrape/regional → GET /jobs/{id} → GET /jobs/{id}/result → GET /jobs/{id}/download
   ```

2. **Manejo de Errores:**
   - Job no encontrado
   - Job de tipo incorrecto
   - Job no completado
   - Archivo CSV no existe
   - Errores durante el scraping

## Ejecutar Tests

### Ejecutar todos los tests de API:
```bash
pytest tests_api/ -v
```

### Ejecutar solo tests de scrape regional:
```bash
pytest tests_api/test_regional_scrape_api.py -v
```

### Ejecutar solo tests de jobs:
```bash
pytest tests_api/test_jobs_api_complete.py -v
```

### Ejecutar un test específico:
```bash
pytest tests_api/test_regional_scrape_api.py::TestRegionalScrapeAPI::test_regional_scrape_full_flow -v
```

## Mejoras Implementadas

1. **Uso de `tmp_path` fixture de pytest**: Evita problemas con archivos temporales en Windows
2. **Mocks apropiados**: Usa `AsyncMock` para funciones async
3. **Esperas inteligentes**: Espera a que los jobs completen antes de verificar resultados
4. **Cobertura completa**: Cubre casos exitosos y de error
5. **Validaciones exhaustivas**: Verifica estructura de respuestas y contenido

## Próximos Pasos

- [ ] Ejecutar tests en CI/CD
- [ ] Agregar tests de integración con scraper real (opcional, más lentos)
- [ ] Agregar tests de rendimiento si es necesario
- [ ] Documentar casos de uso específicos
