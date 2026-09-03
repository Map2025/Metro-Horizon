import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

class MorosidadService:
    def __init__(self):
        # Un pipeline sencillo con imputación, escalado y un RandomForest
        self.model = Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
        ])
        self.is_trained = False

    def _preparar_datos(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ml = df.copy()
        
        # Convertir fechas a datetime si no lo están
        df_ml['FechaUltimoRecibo'] = pd.to_datetime(df_ml['FechaUltimoRecibo'])
        df_ml['FechaPrimeraFactura'] = pd.to_datetime(df_ml['FechaPrimeraFactura'])
        
        hoy = pd.Timestamp.today()
        
        # Calcular Días de Atraso (desde el último recibo, o desde la primera factura si nunca pagó)
        df_ml['DiasDesdeUltimoPago'] = np.where(
            df_ml['FechaUltimoRecibo'].notna(),
            (hoy - df_ml['FechaUltimoRecibo']).dt.days,
            (hoy - df_ml['FechaPrimeraFactura']).dt.days
        )
        # Rellenar con 0 por si hay datos extraños
        df_ml['DiasDesdeUltimoPago'] = df_ml['DiasDesdeUltimoPago'].fillna(0)
        
        # Target: Es considerado moroso severo si lleva más de 45 días sin pagar y tiene saldo deudor
        df_ml['EsMoroso'] = np.where(df_ml['DiasDesdeUltimoPago'] > 45, 1, 0)
        
        return df_ml

    def entrenar_modelo(self, df_historico: pd.DataFrame):
        df_ml = self._preparar_datos(df_historico)
        features = ['SaldoActual', 'DiasDesdeUltimoPago']
        
        X = df_ml[features]
        y = df_ml['EsMoroso']
        
        self.model.fit(X, y)
        self.is_trained = True

    def predecir_riesgo(self, df_nuevos: pd.DataFrame) -> pd.DataFrame:
        if not self.is_trained:
            self.entrenar_modelo(df_nuevos)
            
        df_ml = self._preparar_datos(df_nuevos)
        features = ['SaldoActual', 'DiasDesdeUltimoPago']
        X = df_ml[features]
        
        # Probabilidad de ser clase 1 (Moroso)
        clf = self.model.named_steps['classifier']
        if len(clf.classes_) == 1:
            # Si todos los datos históricos eran de una sola clase (ej. todos morosos o todos al día)
            if clf.classes_[0] == 1:
                probabilidades = np.ones(len(X))
            else:
                probabilidades = np.zeros(len(X))
        else:
            probabilidades = self.model.predict_proba(X)[:, 1]
        
        df_resultados = df_nuevos.copy()
        df_resultados['Score_Riesgo'] = np.round(probabilidades * 100, 2)
        
        # Asignar categoría de riesgo
        condiciones = [
            (df_resultados['Score_Riesgo'] < 30),
            (df_resultados['Score_Riesgo'] >= 30) & (df_resultados['Score_Riesgo'] < 70),
            (df_resultados['Score_Riesgo'] >= 70)
        ]
        opciones = ['Bajo', 'Medio', 'Alto']
        df_resultados['Nivel_Riesgo'] = np.select(condiciones, opciones)
        
        return df_resultados
