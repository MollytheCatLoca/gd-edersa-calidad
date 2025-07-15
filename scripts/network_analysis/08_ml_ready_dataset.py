#!/usr/bin/env python3
"""
Fase 0 - Script 8: Preparación de Dataset para Machine Learning
==============================================================

Este script integra todas las features calculadas y prepara el dataset final
para modelos de ML, incluyendo:
- Integración de todas las features
- Normalización y escalado
- Codificación de variables categóricas
- Manejo de desbalance de clases
- División en conjuntos de entrenamiento/validación/prueba
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Configuración de rutas
BASE_DIR = Path("/Users/maxkeczeli/Proyects/gd-edersa-calidad")
INPUT_FILE = BASE_DIR / "data/processed/electrical_analysis/transformadores_indices_riesgo.csv"
OUTPUT_DIR = BASE_DIR / "data/processed/electrical_analysis"

# Features a incluir en el modelo
FEATURE_GROUPS = {
    'identificadores': [
        'Codigo', 'Alimentador', 'N_Sucursal', 'N_Localida'
    ],
    'caracteristicas_basicas': [
        'Potencia', 'Q_Usuarios', 'num_circuitos', 
        'Coord_X', 'Coord_Y'
    ],
    'topologicas': [
        'numero_saltos', 'es_nodo_hoja', 'profundidad_arbol',
        'kVA_aguas_abajo', 'usuarios_aguas_abajo', 'num_descendientes',
        'centralidad_intermediacion'
    ],
    'electricas': [
        'distancia_electrica_km', 'R_acumulada', 'X_acumulada', 'Z_acumulada',
        'corriente_estimada_A', 'caida_tension_V', 'caida_tension_percent',
        'tension_estimada_kV', 'indice_debilidad_electrica',
        'hundimiento_arranque_percent'
    ],
    'carga': [
        'kva_por_usuario', 'factor_potencia_estimado', 'factor_diversidad',
        'factor_utilizacion_promedio', 'factor_utilizacion_pico',
        'carga_activa_P_est_kW', 'carga_reactiva_Q_est_kVAR',
        'carga_aparente_S_est_kVA', 'carga_activa_pico_kW',
        'factor_carga', 'indice_carga_reactiva', 'densidad_carga_kW_usuario',
        'margen_reserva', 'indice_sobrecarga'
    ],
    'vulnerabilidad': [
        'indice_estres_termico_v2', 'temperatura_estimada_rise',
        'factor_perdida_vida', 'años_vida_perdidos_anual',
        'indice_estres_dielectrico', 'probabilidad_descargas_parciales',
        'vulnerabilidad_transitorios', 'indice_vulnerabilidad_compuesto',
        'score_componente_termico', 'score_componente_dielectrico',
        'score_componente_topologico', 'score_componente_vecindario'
    ],
    'vecindario': [
        'num_vecinos_500m', 'tasa_fallas_vecindario', 'tasa_problemas_vecindario',
        'potencia_vecindario_mva', 'usuarios_vecindario', 'riesgo_cascada'
    ],
    'categoricas': [
        'tipo_zona', 'size_category', 'tipo_carga', 'perfil_carga',
        'tipo_conductor', 'sensibilidad_dinamica', 'nivel_estres_termico',
        'nivel_estres_dielectrico', 'nivel_vulnerabilidad', 
        'prioridad_intervencion', 'modo_falla_probable', 'tipo_vecindario',
        'estado_padre', 'nivel_riesgo_sobrecarga'
    ],
    'target': [
        'Resultado'  # Correcta/Penalizada/Fallida
    ]
}

def load_and_validate_data():
    """Cargar y validar datos"""
    print("Cargando datos...")
    df = pd.read_csv(INPUT_FILE)
    
    print(f"✓ {len(df)} registros cargados")
    print(f"✓ {len(df.columns)} columnas disponibles")
    
    # Verificar columnas faltantes
    all_features = []
    for group in FEATURE_GROUPS.values():
        all_features.extend(group)
    
    missing_cols = set(all_features) - set(df.columns)
    if missing_cols:
        print(f"\n⚠️ Columnas faltantes: {missing_cols}")
        # Remover columnas faltantes de los grupos
        for group_name, features in FEATURE_GROUPS.items():
            FEATURE_GROUPS[group_name] = [f for f in features if f in df.columns]
    
    return df

def create_additional_features(df):
    """Crear features adicionales derivadas"""
    print("\nCreando features adicionales...")
    
    # Ratios y productos útiles
    df['impedancia_por_km'] = df['Z_acumulada'] / (df['distancia_electrica_km'] + 0.001)
    df['caida_por_salto'] = df['caida_tension_percent'] / (df['numero_saltos'] + 1)
    df['carga_por_km'] = df['kVA_aguas_abajo'] / (df['distancia_electrica_km'] + 0.001)
    df['vulnerabilidad_termica_dielectrica'] = df['indice_estres_termico_v2'] * df['indice_estres_dielectrico']
    
    # Indicadores binarios
    df['es_sobrecargado'] = (df['indice_sobrecarga'] > 1.0).astype(int)
    df['es_vulnerable'] = (df['indice_vulnerabilidad_compuesto'] > 0.6).astype(int)
    df['tiene_vecinos_problematicos'] = (df['tasa_problemas_vecindario'] > 0.5).astype(int)
    df['caida_fuera_limite'] = (df['caida_tension_percent'] > 5.0).astype(int)
    
    # Interacciones
    df['vulnerabilidad_x_carga'] = df['indice_vulnerabilidad_compuesto'] * df['factor_utilizacion_pico']
    df['distancia_x_carga'] = df['numero_saltos'] * df['kVA_aguas_abajo']
    
    return df

def encode_categorical_features(df, categorical_cols):
    """Codificar variables categóricas"""
    print("\nCodificando variables categóricas...")
    
    df_encoded = df.copy()
    
    # Para cada columna categórica
    for col in categorical_cols:
        if col not in df_encoded.columns:
            continue
            
        # Si tiene pocos valores únicos, usar one-hot encoding
        n_unique = df_encoded[col].nunique()
        
        if n_unique <= 10:
            # One-hot encoding
            dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
            df_encoded = pd.concat([df_encoded, dummies], axis=1)
            df_encoded.drop(col, axis=1, inplace=True)
            print(f"  - {col}: One-hot encoding ({n_unique} categorías)")
        else:
            # Label encoding para muchas categorías
            le = LabelEncoder()
            df_encoded[col + '_encoded'] = le.fit_transform(df_encoded[col].fillna('Unknown'))
            df_encoded.drop(col, axis=1, inplace=True)
            print(f"  - {col}: Label encoding ({n_unique} categorías)")
    
    return df_encoded

def prepare_features_and_target(df_encoded):
    """Preparar features y variable objetivo"""
    print("\nPreparando features y target...")
    
    # Variable objetivo
    target_col = 'Resultado'
    
    # Mapear a valores numéricos para facilitar el ML
    target_mapping = {
        'Correcta': 0,
        'Penalizada': 1,
        'Fallida': 2
    }
    
    y = df_encoded[target_col].map(target_mapping)
    
    # Features (excluir identificadores y target)
    exclude_cols = FEATURE_GROUPS['identificadores'] + [target_col]
    feature_cols = [col for col in df_encoded.columns if col not in exclude_cols]
    
    X = df_encoded[feature_cols].select_dtypes(include=[np.number])
    
    # Llenar valores faltantes
    X = X.fillna(X.median())
    
    print(f"  - Features: {X.shape[1]}")
    print(f"  - Muestras: {X.shape[0]}")
    print(f"  - Distribución del target:")
    for label, count in y.value_counts().items():
        orig_label = [k for k, v in target_mapping.items() if v == label][0]
        print(f"    • {orig_label}: {count} ({count/len(y)*100:.1f}%)")
    
    return X, y, feature_cols

def balance_dataset(X, y, strategy='auto'):
    """Balancear el dataset usando SMOTE"""
    print("\nBalanceando dataset con SMOTE...")
    
    # SMOTE para sobremuestreo sintético
    smote = SMOTE(sampling_strategy=strategy, random_state=42)
    X_balanced, y_balanced = smote.fit_resample(X, y)
    
    print(f"  - Muestras originales: {len(X)}")
    print(f"  - Muestras después de SMOTE: {len(X_balanced)}")
    print(f"  - Distribución balanceada:")
    for label in sorted(y_balanced.unique()):
        count = (y_balanced == label).sum()
        print(f"    • Clase {label}: {count} ({count/len(y_balanced)*100:.1f}%)")
    
    return X_balanced, y_balanced

def scale_features(X_train, X_val, X_test):
    """Normalizar features"""
    print("\nNormalizando features...")
    
    scaler = StandardScaler()
    
    # Ajustar solo con datos de entrenamiento
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    # Convertir de vuelta a DataFrame para mantener nombres de columnas
    X_train_scaled = pd.DataFrame(X_train_scaled, columns=X_train.columns)
    X_val_scaled = pd.DataFrame(X_val_scaled, columns=X_val.columns)
    X_test_scaled = pd.DataFrame(X_test_scaled, columns=X_test.columns)
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler

def analyze_feature_importance(X, y, feature_names):
    """Análisis preliminar de importancia de features"""
    print("\nAnalizando correlación de features con target...")
    
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_selection import mutual_info_classif
    
    # Random Forest para importancia
    rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf.fit(X, y)
    
    # Mutual Information
    mi_scores = mutual_info_classif(X, y, random_state=42)
    
    # Crear DataFrame con scores
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'rf_importance': rf.feature_importances_,
        'mutual_info': mi_scores
    })
    
    # Normalizar scores
    importance_df['rf_importance_norm'] = importance_df['rf_importance'] / importance_df['rf_importance'].sum()
    importance_df['mutual_info_norm'] = importance_df['mutual_info'] / importance_df['mutual_info'].sum()
    
    # Score combinado
    importance_df['combined_score'] = (importance_df['rf_importance_norm'] + importance_df['mutual_info_norm']) / 2
    
    # Ordenar por importancia
    importance_df = importance_df.sort_values('combined_score', ascending=False)
    
    return importance_df

def visualize_data_preparation(df, X_train, y_train, importance_df, save_dir):
    """Visualizar el proceso de preparación de datos"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Distribución del target original
    ax1 = axes[0, 0]
    target_counts = df['Resultado'].value_counts()
    colors = {'Correcta': 'green', 'Penalizada': 'orange', 'Fallida': 'red'}
    target_counts.plot(kind='bar', ax=ax1, color=[colors[x] for x in target_counts.index])
    ax1.set_title('Distribución Original del Target')
    ax1.set_xlabel('Estado')
    ax1.set_ylabel('Cantidad')
    ax1.tick_params(axis='x', rotation=0)
    
    # 2. Top 20 features más importantes
    ax2 = axes[0, 1]
    top_features = importance_df.head(20)
    ax2.barh(range(len(top_features)), top_features['combined_score'])
    ax2.set_yticks(range(len(top_features)))
    ax2.set_yticklabels(top_features['feature'], fontsize=8)
    ax2.set_xlabel('Importancia Combinada')
    ax2.set_title('Top 20 Features Más Importantes')
    ax2.invert_yaxis()
    
    # 3. Correlación entre top features
    ax3 = axes[1, 0]
    top_10_features = importance_df.head(10)['feature'].tolist()
    if all(f in X_train.columns for f in top_10_features):
        corr_matrix = X_train[top_10_features].corr()
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                   center=0, ax=ax3, cbar_kws={'label': 'Correlación'})
        ax3.set_title('Correlación entre Top 10 Features')
    
    # 4. Distribución de vulnerabilidad por clase
    ax4 = axes[1, 1]
    if 'indice_vulnerabilidad_compuesto' in df.columns:
        for i, estado in enumerate(['Correcta', 'Penalizada', 'Fallida']):
            data = df[df['Resultado'] == estado]['indice_vulnerabilidad_compuesto']
            ax4.hist(data, bins=30, alpha=0.6, label=estado, color=list(colors.values())[i])
        ax4.set_xlabel('Índice de Vulnerabilidad')
        ax4.set_ylabel('Frecuencia')
        ax4.set_title('Distribución de Vulnerabilidad por Estado')
        ax4.legend()
    
    plt.tight_layout()
    plt.savefig(save_dir / 'ml_data_preparation.png', dpi=150, bbox_inches='tight')
    plt.close()

def save_ml_datasets(X_train, X_val, X_test, y_train, y_val, y_test, 
                    feature_names, scaler, importance_df):
    """Guardar datasets preparados para ML"""
    print("\nGuardando datasets...")
    
    # Crear directorio para ML
    ml_dir = OUTPUT_DIR / "ml_datasets"
    ml_dir.mkdir(exist_ok=True)
    
    # Guardar datasets
    datasets = {
        'X_train': X_train,
        'X_val': X_val,
        'X_test': X_test,
        'y_train': y_train,
        'y_val': y_val,
        'y_test': y_test
    }
    
    for name, data in datasets.items():
        if isinstance(data, pd.DataFrame):
            data.to_csv(ml_dir / f"{name}.csv", index=False)
        else:
            pd.DataFrame(data, columns=['target']).to_csv(
                ml_dir / f"{name}.csv", index=False
            )
    
    # Guardar metadatos
    metadata = {
        'n_features': len(feature_names),
        'feature_names': feature_names,
        'n_train': len(X_train),
        'n_val': len(X_val),
        'n_test': len(X_test),
        'target_mapping': {
            'Correcta': 0,
            'Penalizada': 1,
            'Fallida': 2
        },
        'top_30_features': importance_df.head(30).to_dict('records')
    }
    
    with open(ml_dir / 'metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Guardar scaler
    import joblib
    joblib.dump(scaler, ml_dir / 'scaler.pkl')
    
    # Guardar importancia de features
    importance_df.to_csv(ml_dir / 'feature_importance.csv', index=False)
    
    print(f"✓ Datasets guardados en: {ml_dir}")

def main():
    """Función principal"""
    print("=" * 80)
    print("PREPARACIÓN DE DATASET PARA MACHINE LEARNING")
    print("=" * 80)
    
    # Cargar datos
    df = load_and_validate_data()
    
    # Crear features adicionales
    df = create_additional_features(df)
    
    # Codificar categóricas
    categorical_cols = [col for col in FEATURE_GROUPS['categoricas'] if col in df.columns]
    df_encoded = encode_categorical_features(df, categorical_cols)
    
    # Preparar features y target
    X, y, feature_names = prepare_features_and_target(df_encoded)
    
    # División inicial (antes de balancear)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp
    )  # 0.176 * 0.85 ≈ 0.15, para tener 70/15/15
    
    print(f"\nDivisión de datos:")
    print(f"  - Entrenamiento: {len(X_train)} ({len(X_train)/len(X)*100:.1f}%)")
    print(f"  - Validación: {len(X_val)} ({len(X_val)/len(X)*100:.1f}%)")
    print(f"  - Prueba: {len(X_test)} ({len(X_test)/len(X)*100:.1f}%)")
    
    # Balancear solo el conjunto de entrenamiento
    X_train_balanced, y_train_balanced = balance_dataset(X_train, y_train)
    
    # Escalar features
    X_train_scaled, X_val_scaled, X_test_scaled, scaler = scale_features(
        X_train_balanced, X_val, X_test
    )
    
    # Análisis de importancia de features
    importance_df = analyze_feature_importance(X_train_balanced, y_train_balanced, feature_names)
    
    # Visualizaciones
    viz_dir = OUTPUT_DIR / "visualizations"
    viz_dir.mkdir(exist_ok=True)
    visualize_data_preparation(df, X_train_balanced, y_train_balanced, importance_df, viz_dir)
    print(f"✓ Visualizaciones guardadas")
    
    # Guardar datasets
    save_ml_datasets(
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train_balanced, y_val, y_test,
        feature_names, scaler, importance_df
    )
    
    # Generar reporte final
    report = {
        'timestamp': datetime.now().isoformat(),
        'datos_originales': {
            'total_registros': len(df),
            'total_columnas': len(df.columns),
            'distribucion_target': df['Resultado'].value_counts().to_dict()
        },
        'preparacion': {
            'features_creadas': len(feature_names),
            'features_categoricas_codificadas': len(categorical_cols),
            'valores_faltantes_imputados': X.isnull().sum().sum()
        },
        'division_datos': {
            'train_original': len(X_train),
            'train_balanceado': len(X_train_balanced),
            'validation': len(X_val),
            'test': len(X_test)
        },
        'top_10_features': importance_df.head(10)[['feature', 'combined_score']].to_dict('records'),
        'estadisticas_features': {
            'media_importancia': importance_df['combined_score'].mean(),
            'std_importancia': importance_df['combined_score'].std(),
            'features_alta_importancia': len(importance_df[importance_df['combined_score'] > 0.01])
        }
    }
    
    report_file = OUTPUT_DIR / "ml_preparation_report.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Reporte guardado en: {report_file}")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)
    print(f"• Dataset ML preparado con {len(feature_names)} features")
    print(f"• Entrenamiento: {len(X_train_balanced)} muestras (balanceado)")
    print(f"• Validación: {len(X_val)} muestras")
    print(f"• Prueba: {len(X_test)} muestras")
    print("\nTop 5 Features más importantes:")
    for _, row in importance_df.head(5).iterrows():
        print(f"  - {row['feature']}: {row['combined_score']:.4f}")
    
    print("\n✅ Dataset listo para entrenamiento de modelos ML")
    print("   Próximos pasos:")
    print("   1. Entrenar modelos (Random Forest, XGBoost, Neural Networks)")
    print("   2. Optimizar hiperparámetros")
    print("   3. Evaluar con métricas apropiadas (F1, AUC-ROC, etc.)")
    print("   4. Interpretar resultados para acciones de mantenimiento")

if __name__ == "__main__":
    main()