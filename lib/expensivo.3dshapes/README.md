3D models
=========

For KiCad's 3D viewer. Not covered by this repository's CC BY 4.0 license;
each file keeps its own:

| File | From | License |
|------|------|---------|
| `SW_Hotswap_Kailh.wrl`, `.step` | [mayjs/keyswitch-kicad-library](https://github.com/mayjs/keyswitch-kicad-library) `modules/packages3d/Switch_Keyboard_Kailh.3dshapes` @ f9c7d57 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode), with the KiCad library exception for designs using it |
| `SW_Cherry_MX_PCB.wrl`, `.step` | same, `Switch_Keyboard_Cherry_MX.3dshapes` | same |
| `Keycap_DSA_1u.wrl` | [anhthang/dsa-keycap](https://github.com/anhthang/dsa-keycap) `DSA 1u.stl`, reduced to 6000 faces and converted with `scripts/stl_to_wrl.py` | MIT (Copyright (c) 2020 Anh Thang), see `LICENSE-dsa-keycap.txt` |

The nice!nano model is not in the repository: it is
[infused-kim/kb_ergogen_fp](https://github.com/infused-kim/kb_ergogen_fp)'s
`Nice_Nano_V2.step`, licensed CC BY-NC-SA 4.0, which `scripts/build.sh`
downloads to `build/3d/`.
