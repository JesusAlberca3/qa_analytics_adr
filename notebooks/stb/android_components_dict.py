"""
este diccionario se basa en la documentación oficial de Android Developers
es un apoyo para el diagnostico de los logs de Android TV (STB)

Clasificación:
- SYSTEM: Componentes del sistema Android (ruido, ignorar en análisis)
- APP: Componentes de aplicación (críticos)
- MEDIA: Codecs y reproducción
- DRM: Seguridad y licencias
- CUSTOM: Componentes específicos de vendor (MediaTek, etc.)

formato para agregar un nuevo componente:
'NuevoComponente': {
    'categoria': 'APP',
    'descripcion': 'Descripción del componente',
    'doc_oficial': 'URL de la documentación oficial',
    'severidad_tipica': 'ALTA',
    'errores_comunes': [
        'Error común 1',
        'Error común 2'
    ],
    'accion': 'Acción recomendada'
}





"""
ANDROID_COMPONENTS = {


    'PqLink': {
        'categoria': 'CUSTOM',
        'descripcion': 'Sony Picture Quality Engine (propietario) - post-processing de video',
        'doc_oficial': 'N/A (Sony proprietary component)',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Errores observados en logs pero no documentados públicamente',
            'Componente propietario de Sony sin documentación pública'
        ],
        'causas_saturacion': [
            'No documentado - componente propietario de Sony'
        ],
        'accion': 'Componente propietario - escalar a soporte de Sony si persiste'
    },



    'BufferQueueProducer': {
        'categoria': 'SYSTEM',
        'descripcion': 'Producer side of BufferQueue - manages graphics buffer allocation',
        'doc_oficial': 'https://source.android.com/docs/core/graphics/arch-bq-gralloc',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'queueBuffer: BufferQueue has been abandoned',
            'dequeueBuffer: no buffer available',
            'Connection lost - consumer disconnected'
        ],
        'causas_saturacion': [
            'Consumer no procesa buffers a tiempo (buffer starvation)',
            'Producer genera frames más rápido que consumer puede procesar',
            'Memory pressure impide allocar nuevos buffers'
        ],
        'accion': 'Revisar consumer side del BufferQueue, verificar frame rate vs processing capacity'
    },

    'gralloc4': {
        'categoria': 'SYSTEM',
        'descripcion': 'Graphics Memory Allocator HAL 4.0 - GPU memory management',
        'doc_oficial': 'https://source.android.com/docs/core/graphics/implement-gralloc',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Failed to allocate buffer',
            'Out of memory for graphics allocation',
            'Invalid buffer handle',
            'Invalid usage bits',
            'Memory exhaustion'
        ],
        'causas_saturacion': [
            'Memoria gráfica insuficiente (GPU memory exhausted)',
            'Memory leaks - buffers no liberados correctamente',
            'Fragmentación de memoria GPU'
        ],
        'accion': 'Verificar memory leaks en rendering pipeline, revisar liberación de buffers. Ignorar si < 100 errors'
    },

    'RenderEngine': {
        'categoria': 'SYSTEM',
        'descripcion': 'SurfaceFlinger rendering engine - composes surfaces to display',
        'doc_oficial': 'https://source.android.com/docs/core/graphics/surfaceflinger',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Failed to create EGLSurface',
            'eglMakeCurrent failed',
            'Composition timeout',
            'Shader compilation errors',
            'GL context issues'
        ],
        'causas_saturacion': [
            'GPU overload por composición compleja de múltiples layers',
            'Problemas con EGL context (OpenGL ES)',
            'Display HAL no responde a tiempo'
        ],
        'accion': 'Reducir complejidad de composición, revisar número de layers activos. Si > 50 errors, verificar drivers GPU'
    },

   
    # Componentes del sistema Android (RUIDO)
     

    'ActivityManager': {
        'categoria': 'SYSTEM',
        'descripcion': 'Manages app lifecycle, activities, services, and broadcasts',
        'doc_oficial': 'https://developer.android.com/reference/android/app/ActivityManager',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Broadcast failures (protected/non-protected mismatch)',
            'Background execution restrictions (Android 8+)',
            'Service start failures',
            'ANR (Application Not Responding)'
        ],
        'accion': 'Revisar si app tiene permisos correctos para broadcasts'
    },

    'system_server': {
        'categoria': 'SYSTEM',
        'descripcion': 'Core Android system process that hosts system services',
        'doc_oficial': 'https://source.android.com/docs/core/runtime',
        'severidad_tipica': 'MEDIA',
        'errores_comunes': [
            'Binder transaction failures',
            'System service crashes',
            'Permission denials'
        ],
        'accion': 'Errors aquí indican problemas sistémicos, no de app'
    },

    'SELinux': {
        'categoria': 'SYSTEM',
        'descripcion': 'Security-Enhanced Linux - Android security policy enforcement',
        'doc_oficial': 'https://source.android.com/docs/security/features/selinux',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'avc: denied (permission denials)',
            'Context mismatches',
            'Policy violations'
        ],
        'accion': 'Ignorar en análisis de app - es ruido de sistema'
    },

    'TaskPersister': {
        'categoria': 'SYSTEM',
        'descripcion': 'Persists recent tasks to disk',
        'doc_oficial': 'https://cs.android.com/android/platform/superproject/+/master:frameworks/base/services/core/java/com/android/server/wm/TaskPersister.java',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Failed to save task snapshot',
            'IOException writing tasks'
        ],
        'accion': 'Ignorar - no afecta funcionalidad de app'
    },

    'TimeStats': {
        'categoria': 'SYSTEM',
        'descripcion': 'SurfaceFlinger time statistics tracking',
        'doc_oficial': 'https://source.android.com/docs/core/graphics/surfaceflinger',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Stats recording failures'
        ],
        'accion': 'Ignorar - solo telemetría'
    },

    'DropBoxTask': {
        'categoria': 'SYSTEM',
        'descripcion': 'Writes crash logs to DropBoxManager',
        'doc_oficial': 'https://developer.android.com/reference/android/os/DropBoxManager',
        'severidad_tipica': 'INFO',
        'errores_comunes': [
            'Failed to write crash dump',
            'Storage full'
        ],
        'accion': 'Indica que hubo crash - revisar qué componente crasheó'
    },

    'VerityUtils': {
        'categoria': 'SYSTEM',
        'descripcion': 'File system integrity verification',
        'doc_oficial': 'https://source.android.com/docs/security/features/verifiedboot',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Verity check failures'
        ],
        'accion': 'Ignorar - seguridad del sistema'
    },

    'ArtManagerService': {
        'categoria': 'SYSTEM',
        'descripcion': 'Android Runtime optimization service',
        'doc_oficial': 'https://source.android.com/docs/core/runtime/configure',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Compilation failures',
            'Dex optimization errors'
        ],
        'accion': 'Ignorar - optimización de sistema'
    },

    'BpTransactionCompletedListener': {
        'categoria': 'SYSTEM',
        'descripcion': 'SurfaceFlinger transaction callback',
        'doc_oficial': 'https://source.android.com/docs/core/graphics/surfaceflinger',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Transaction callback failures'
        ],
        'accion': 'Ignorar - interno de rendering pipeline'
    },

    # ========================================================================
    # APP - Componentes de aplicación (IMPORTANTES)
    # ========================================================================

    'AppSearchManagerService': {
        'categoria': 'APP',
        'descripcion': 'On-device search indexing service',
        'doc_oficial': 'https://developer.android.com/reference/android/app/appsearch/AppSearchManager',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'IllegalStateException: User is locked or not running',
            'Storage access failures',
            'Index corruption'
        ],
        'accion': 'Verificar multi-user state antes de search operations'
    },

    'GPUAUX': {
        'categoria': 'APP',
        'descripcion': 'GPU auxiliary rendering (likely vendor-specific)',
        'doc_oficial': 'https://developer.android.com/topic/performance/rendering',
        'severidad_tipica': 'MEDIA',
        'errores_comunes': [
            'Texture allocation failures',
            'Shader errors',
            'Frame buffer issues'
        ],
        'accion': 'Si > 100 errors, reducir carga GPU (imágenes, efectos)'
    },

    'TraceManagerImpl': {
        'categoria': 'APP',
        'descripcion': 'Application tracing/logging (likely custom)',
        'doc_oficial': 'https://developer.android.com/topic/performance/tracing',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Trace buffer full',
            'Failed to write trace'
        ],
        'accion': 'Ignorar - solo telemetría'
    },

    # ========================================================================
    # MEDIA - Codecs y reproducción (CRÍTICOS PARA VIDEO)
    # ========================================================================

    'OMXNodeInstance': {
        'categoria': 'MEDIA',
        'descripcion': 'OpenMAX IL codec component instance',
        'doc_oficial': 'https://source.android.com/docs/core/media/omx',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Buffer allocation failed',
            'Port configuration mismatch',
            'Codec initialization failed',
            'acquireBuffer timeout'
        ],
        'accion': 'Verificar codec support, buffer size, DRM tokens'
    },

    'MtkOmxVdec': {
        'categoria': 'MEDIA',
        'descripcion': 'MediaTek OMX video decoder',
        'doc_oficial': 'https://source.android.com/docs/core/media/omx',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Decoder configuration errors',
            'Frame decode failures',
            'Buffer overflow'
        ],
        'accion': 'Problema de decoder - verificar stream codec/bitrate'
    },

    'MtkOmxCore': {
        'categoria': 'MEDIA',
        'descripcion': 'MediaTek OMX core library',
        'doc_oficial': 'https://source.android.com/docs/core/media/omx',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Component loading failures',
            'Library initialization errors'
        ],
        'accion': 'Error en core OMX - posible problema de drivers'
    },

    'ACodec': {
        'categoria': 'MEDIA',
        'descripcion': 'Android MediaCodec wrapper over OMX',
        'doc_oficial': 'https://developer.android.com/reference/android/media/MediaCodec',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Codec configuration exception',
            'Input buffer dequeue timeout',
            'Output format changed errors'
        ],
        'accion': 'Verificar configuración de MediaCodec y formato de stream'
    },

    'VCodecDrv': {
        'categoria': 'MEDIA',
        'descripcion': 'Video codec driver (vendor-specific)',
        'doc_oficial': 'https://source.android.com/docs/core/media',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'Driver initialization failed',
            'Hardware codec errors'
        ],
        'accion': 'Problema de driver - posible issue de firmware'
    },

    'GRM': {
        'categoria': 'MEDIA',
        'descripcion': 'Graphics Resource Manager (likely vendor)',
        'doc_oficial': 'https://source.android.com/docs/core/graphics',
        'severidad_tipica': 'MEDIA',
        'errores_comunes': [
            'Resource allocation failures',
            'Memory management errors'
        ],
        'accion': 'Verificar memoria disponible para rendering'
    },

    # ========================================================================
    # DRM - Seguridad y licencias (CRÍTICOS PARA DRM)
    # ========================================================================

    'WVCdm': {
        'categoria': 'DRM',
        'descripcion': 'Widevine Content Decryption Module',
        'doc_oficial': 'https://source.android.com/docs/core/media/drm',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'License acquisition failed',
            'Decryption errors',
            'Session timeout'
        ],
        'accion': 'Verificar licencias DRM, tokens, conectividad con servidor'
    },

    'PlayReadyUtil': {
        'categoria': 'DRM',
        'descripcion': 'Microsoft PlayReady DRM utility',
        'doc_oficial': 'https://learn.microsoft.com/playready/',
        'severidad_tipica': 'ALTA',
        'errores_comunes': [
            'UUID validation failures',
            'License parsing errors',
            'Crypto initialization failed'
        ],
        'accion': 'Verificar PlayReady licenses y servidor de licencias'
    },

    # ========================================================================
    # CUSTOM - Vendor-specific (MEDIATEK)
    # ========================================================================

    'TimeMsgProcess': {
        'categoria': 'CUSTOM',
        'descripcion': 'MediaTek time synchronization process',
        'doc_oficial': 'N/A (vendor-specific)',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Time sync feature not enabled',
            'Network time server unreachable'
        ],
        'accion': 'Ignorar - feature opcional de time sync'
    },

    'AgentTimeActionReceiver': {
        'categoria': 'CUSTOM',
        'descripcion': 'MediaTek time action broadcast receiver',
        'doc_oficial': 'N/A (vendor-specific)',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Broadcast delivery failures'
        ],
        'accion': 'Ignorar - related a TimeMsgProcess'
    },

    'HidlServiceManagement': {
        'categoria': 'CUSTOM',
        'descripcion': 'HAL Interface Definition Language service manager',
        'doc_oficial': 'https://source.android.com/docs/core/architecture/hidl',
        'severidad_tipica': 'MEDIA',
        'errores_comunes': [
            'Service registration failures',
            'HIDL transport errors'
        ],
        'accion': 'Problema de HAL - verificar vendor implementation'
    },

    'libhidlmemory': {
        'categoria': 'CUSTOM',
        'descripcion': 'HIDL shared memory library',
        'doc_oficial': 'https://source.android.com/docs/core/architecture/hidl',
        'severidad_tipica': 'MEDIA',
        'errores_comunes': [
            'Shared memory allocation failures'
        ],
        'accion': 'Verificar memoria disponible para IPC'
    },

    'katniss_search_TraceManagerImpl': {
        'categoria': 'CUSTOM',
        'descripcion': 'Custom search trace manager (app-specific)',
        'doc_oficial': 'N/A (application code)',
        'severidad_tipica': 'BAJA',
        'errores_comunes': [
            'Trace logging failures'
        ],
        'accion': 'Código de app - revisar implementation'
    },
    '<MI_PQ>': {
        'categoria': 'CUSTOM',
        'descripcion': 'MediaTek Picture Quality Module - procesamiento de imagen en Smart TV',
        'doc_oficial': 'N/A (MediaTek proprietary)',
        'severidad_tipica': 'CRÍTICA',
        'errores_comunes': [
            'Invalid Window ID - display manager perdió referencia al panel',
            'GetHistogram failed - no puede leer datos del panel LCD',
            'ioctl failed - driver de display no responde'
        ],
        'causas_saturacion': [
            'Display driver crasheó o entró en estado inválido',
            'Panel LCD no responde (problema de hardware)',
            'Memory corruption en GPU/display buffers'
        ],
        'accion': 'CRÍTICO - TV inutilizable. Forzar reinicio (desconectar corriente)'
    },

    'PQ_HIDL': {
        'categoria': 'SYSTEM',
        'descripcion': 'Picture Quality Hardware Abstraction Layer (MediaTek)',
        'doc_oficial': 'https://source.android.com/docs/core/architecture/hidl',
        'severidad_tipica': 'CRÍTICA',
        'errores_comunes': [
            'mGetHistogram failed - HAL no puede comunicarse con hardware',
            'PQ dequeue failed - queue de comandos bloqueada',
            'str_params is empty - parámetros inválidos'
        ],
        'causas_saturacion': [
            'Driver de PQ no responde',
            'Hardware MediaTek en estado inválido',
            'Kernel panic en módulo de display'
        ],
        'accion': 'HAL corrupto - reiniciar display service, verificar logs de kernel'
    },

    'HuiVout': {
        'categoria': 'CUSTOM',
        'descripcion': 'Hisense Video Output Module (propietario) - conecta SoC con panel LCD',
        'doc_oficial': 'N/A (Hisense proprietary)',
        'severidad_tipica': 'CRÍTICA',
        'errores_comunes': [
            'mDispLink set to NULL - conexión con panel LCD perdida',
            'HUI_VOutPerstreamDeInit - output de video desconectado'
        ],
        'causas_saturacion': [
            'Video output perdió conexión con panel LCD físico',
            'TCON board (timing controller) no responde',
            'GPU entró en estado inválido'
        ],
        'accion': 'Display físico desconectado - verificar hardware, actualizar firmware Hisense'
    },



}




# Función helper para clasificar
def get_component_info(tag):
    """Retorna info del componente si existe"""
    return ANDROID_COMPONENTS.get(tag, None)


def is_system_noise(tag):
    """Determina si un tag es ruido del sistema"""
    info = get_component_info(tag)
    if info is None:
        return False
    return info['categoria'] == 'SYSTEM' and info['severidad_tipica'] == 'BAJA'


def get_critical_components(tags_with_errors):
    """
    Filtra solo componentes críticos (APP, MEDIA, DRM)
    Retorna dict con tag -> info
    """
    critical = {}
    for tag, count in tags_with_errors.items():
        info = get_component_info(tag)
        if info and info['categoria'] in ['APP', 'MEDIA', 'DRM']:
            critical[tag] = {
                'count': count,
                'info': info
            }
    return critical


if __name__ == "__main__":
    # Test
    print(f"Total componentes documentados: {len(ANDROID_COMPONENTS)}")
    print(f"\nPor categoría:")
    
    categorias = {}
    for tag, info in ANDROID_COMPONENTS.items():
        cat = info['categoria']
        categorias[cat] = categorias.get(cat, 0) + 1
    
    for cat, count in sorted(categorias.items()):
        print(f"  {cat}: {count}")