# Demo run instructions

## Python (reference)
```bash
python src/python/image_io_demo.py
```

### Spatial focus demo (moving dot)

```bash
# from repo root
PYTHONPATH=src/python python src/python/demos/spatial_focus_demo.py
```

## Java (Maven/IntelliJ)
- Set main class: `ai.nektron.grownet.ImageIODemo`
- Ensure Region has the Java patch (`tickImage`, `addInputLayer2D`, `addOutputLayer2D`).
- Run.

## C++ (CLion/CMake)
- Add to your CMakeLists:
  ```cmake
  add_executable(image_io_demo
      src/cpp/ImageIODemo.cpp
      # plus sources that define Region/Layer/Neuron/Weight etc.
  )
  target_include_directories(image_io_demo PRIVATE src/cpp)
  ```
- Ensure Region has `tickImage` and `getLayers()` accessors (see docs/REGION_PATCH_CPP.md).
- Build and run the `image_io_demo` target.

## Mojo
- Ensure `mojo/Region.mojo` has factories and `tick_image` (see docs/REGION_PATCH_MOJO.md).
- Run the demo:
  ```bash
  mojo run mojo/image_io_demo.mojo
  ```
- You should see logs every 5 steps with delivered events and simple counts.
