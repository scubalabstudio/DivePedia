# システムチャート データファイル

## ファイル構成

### 元ファイル
- `extracted_system_charts.json` - 全カメラのシステムチャートデータ（19,545行、約2MB）

### カメラ別分割ファイル
`camera/` ディレクトリに各カメラごとのJSONファイルを格納

#### Canon カメラ（19機種）
- `Canon_1DXMKII.json`
- `Canon_1DXMKIII.json`
- `Canon_5DMKIV.json`
- `Canon_5DSR.json`
- `Canon_6DMKII.json`
- `Canon_7DMKII.json`
- `Canon_80D.json`
- `Canon_EOS_5D_Mark_III.json`
- `Canon_EOS_5D_Mark_IV.json`
- `Canon_EOS_6D.json`
- `Canon_EOS_70D.json`
- `Canon_EOS_7D_Mark_II.json`
- `Canon_EOS_80D.json`
- `Canon_EOS_R.json`
- `Canon_EOS_R5.json`
- `Canon_EOS R.json`
- `Canon_R1.json`
- `Canon_R3.json`
- `Canon_R5.json`
- `Canon_R5C.json`
- `Canon_R5II.json`
- `Canon_R6.json`
- `Canon_R6II.json`

#### Nikon カメラ（15機種）
- `Nikon_D5.json`
- `Nikon_D6.json`
- `Nikon_D500.json`
- `Nikon_D750.json`
- `Nikon_D780.json`
- `Nikon_D810.json`
- `Nikon_D850.json`
- `Nikon_D7200.json`
- `Nikon_D7500.json`
- `Nikon_Z5II.json`
- `Nikon_Z6.json`
- `Nikon_Z6II.json`
- `Nikon_Z6III.json`
- `Nikon_Z7.json`
- `Nikon_Z7II.json`
- `Nikon_Z8.json`
- `Nikon_Z9.json`

#### SONY カメラ（6機種）
- `SONY_α1.json`
- `SONY_α7IV.json`
- `SONY_α7RIV.json`
- `SONY_α7RV.json`
- `SONY_α7sIII.json`
- `SONY_α9II.json`

#### Panasonic カメラ（4機種）
- `Panasonic_S1H.json`
- `Panasonic_S1R.json`
- `Panasonic_S1RII.json`
- `Panasonic_S5II.json`

#### Fujifilm カメラ（4機種）
- `Fujifilm_GFX100.json`
- `Fujifilm_GFX100II.json`
- `Fujifilm_GFX100S.json`
- `Fujifilm_GFX50S.json`

#### Olympus/OM System カメラ（9機種）
- `E-PL9.json`
- `E-PL10.json`
- `OLYMPUS_OM-D_E-M5_Mark_III.json`
- `OM-D_E-M5_Mark_III.json`
- `OM_SYSTEMS_OM-5.json`
- `OM_SYSTEM_E-M10_Mark_IV.json`
- `OM_SYSTEM_OM-5.json`
- `OM_SYSTEM_OM1.json`
- `OM_SYSTEM_OM1_Mark_II.json`

#### コンパクトカメラ（5機種）
- `TG-3.json`
- `TG-4.json`
- `TG-5.json`
- `TG-6.json`
- `TG-7.json`

## データ統計

### 総件数
- **📁 JSONファイル数**: 68個
- **📋 総データ件数**: **7,314件**

### ブランド別データ数
- **Canon**: 23機種、3,179件
- **Nikon**: 17機種、1,380件
- **SONY**: 6機種、777件
- **Panasonic**: 4機種、352件
- **Fujifilm**: 4機種、152件
- **OM System/Olympus**: 9機種、514件
- **コンパクトカメラ（TG）**: 5機種、23件

### 主要機種のデータ数
- **Canon EFマウント系**: 各323件（1DXMKII、1DXMKIII、5DMKIV、5DSR、6DMKII、7DMKII、80D）
- **Canon EOS R系**: 各86件（R1、R3、R5、R5C、R5II、R6、R6II）
- **Nikon Dシリーズ**: 各124件（D5、D500、D6、D7200、D750、D7500、D780、D810、D850）
- **Nikon Zシリーズ**: 各102件（Z6、Z6II、Z7、Z8、Z9）、Z7IIは204件
- **SONY α7RIV**: 222件（最多）
- **その他SONY α**: 各111件

### 重複データ
- **重複除去後**: 4,478件（重複率：約39%）
- **Supabase登録済み**: 4,478件（extension3対応）

## データ構造
各JSONファイルは以下の構造の配列です：
```json
[
  {
    "camera": "カメラ名",
    "housing": "ハウジング名",
    "lens": "レンズ名または null",
    "gear": "ギア名または null",
    "adapter": "アダプタ名または null",
    "extension1": "エクステンション1または null",
    "extension2": "エクステンション2または null", 
    "extension3": "エクステンション3または null",
    "port": "ポート名または null"
  }
]
```

## 生成方法
`split_by_camera.py` スクリプトを使用して元ファイルからカメラ別に分割。

## Supabaseインポート
`script/gear/reset_db_and_import.py` を使用してSupabaseにインポート済み。重複除去により最適化されたデータが格納されています。