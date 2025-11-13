########################################################################
# CMakeLists.txt
#
# Author: Matthias Moller
# Copyright (C) 2021-2025 by the IgaNet authors
#
# This file is part of the IgaNet project
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# CMakeLists.txt accepts the following command line parameters
#
# PYIGANET_COEFF_TYPE
#
########################################################################

cmake_minimum_required (VERSION 3.24)

include(FetchContent)

########################################################################
#
# Project: IgANet-Python
#
########################################################################
project(IgANet-Python)

add_library(iganet_python INTERFACE)
add_library(iganet::python ALIAS iganet_python)

target_include_directories(iganet_python INTERFACE ${PROJECT_BINARY_DIR}/pyiganet/csrc ${PROJECT_SOURCE_DIR}/pyiganet/csrc)

########################################################################
# IgANets (core)
########################################################################
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)

  if(EXISTS "${CMAKE_SOURCE_DIR}/.git")
    FetchContent_Declare(
      iganet_core
      GIT_REPOSITORY https://github.com/iganets/iganet.git
      GIT_TAG main
    )
  else()  
    FetchContent_Declare(
      iganet_core
      URL https://github.com/iganets/iganet/archive/refs/heads/main.zip
    )
  endif()
     
  FetchContent_MakeAvailable(iganet_core)
  FetchContent_GetProperties(iganet_core)
  
  ######################################################################
  # Set C++ standard
  ######################################################################
  set(CMAKE_CXX_STANDARD 20)
  set(CMAKE_CXX_STANDARD_REQUIRED ON)
  set(CMAKE_CXX_EXTENSIONS OFF)

  ######################################################################
  # Find libtorch_python library
  ######################################################################
  find_package(Torch)
  set(TORCH_LIBRARIES "")
  append_torchlib_if_found(torch_python)
  target_link_libraries(iganet_python INTERFACE ${TORCH_LIBRARIES})
endif()

########################################################################
# Pybind11
########################################################################
list(APPEND CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake")
include(pybind11)

########################################################################
# Options
########################################################################
# Set a default coefficient numeric types if not specified
if(NOT PYIGANET_COEFF_TYPE)
  set(PYIGANET_COEFF_TYPE double CACHE STRING
    "Coefficient type(float, double)" FORCE)
endif()
set_property(CACHE PYIGANET_COEFF_TYPE PROPERTY STRINGS "float" "double")

message("")
message("PyIgANet options:")
message("PYIGANET_COEFF_TYPE................: ${PYIGANET_COEFF_TYPE}")
message("")

########################################################################
# Auto-generate source files
########################################################################

# Clean output directory
file(GLOB_RECURSE FILES_AND_DIRS "${PROJECT_BINARY_DIR}/pyiganet/*")
foreach(ITEM ${FILES_AND_DIRS})
  file(REMOVE_RECURSE ${ITEM})
endforeach()

# Config
configure_file(${PROJECT_SOURCE_DIR}/pyiganet/csrc/pyconfig.hpp.in
  ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyconfig.hpp @ONLY)

# Create list of PyBind11 init subroutines
list(APPEND init_core "init_options")

# Explicit instantiation of templated blocktensor classes
foreach(ROWS RANGE 1 2)
  foreach(COLS RANGE 1 2)

    set(SUFFIX "_${ROWS}_${COLS}")
    list(APPEND init_core "init_BlockTensor${SUFFIX}")

    configure_file(${PROJECT_SOURCE_DIR}/pyiganet/csrc/pyblocktensor.cxx.in
      ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyblocktensor${SUFFIX}.cxx @ONLY)
  endforeach()
endforeach()

# Create list of PyBind11 init subroutines
list(APPEND init_splines "init_bspline")

# Explicit instantiation of templated spline classes
foreach(GEODIM RANGE 1 2)
  foreach(DEGREES IN ITEMS
      "1" "1,1")# "1,1,1" "1,1,1,1")
#      "2" "2,2" "2,2,2" "2,2,2,2"
#      "3" "3,3" "3,3,3" "3,3,3,3"
#      "4" "4,4" "4,4,4" "4,4,4,4"
#      "5" "5,5" "5,5,5" "5,5,5,5")

    set(SUFFIX "${GEODIM}d_${DEGREES}")
    string(REPLACE "," "_" SUFFIX ${SUFFIX})
    list(APPEND init_splines "init_UniformBSpline${SUFFIX}")

    string(REPLACE "," ";" PARDIM ${DEGREES})
    list(LENGTH PARDIM PARDIM)

    configure_file(${PROJECT_SOURCE_DIR}/pyiganet/csrc/pybspline.cxx.in
      ${PROJECT_BINARY_DIR}/pyiganet/csrc/pybspline${SUFFIX}.cxx @ONLY)
  endforeach()
endforeach()

# Create main PyIgANet source file
file(WRITE ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
  "/**
   @file pyiganet/pyiganet.cxx

   @brief PyIgANet

   @author Matthias Moller

   @copyright This file is part of the IgANet project

   This Source Code Form is subject to the terms of the Mozilla Public
   License, v. 2.0. If a copy of the MPL was not distributed with this
   file, You can obtain one at http://mozilla.org/MPL/2.0/.
*/

#include <pybind11/pybind11.h>

#include <pyconfig.hpp>

namespace py = pybind11;\n\n")

foreach(init IN LISTS init_core init_splines)
  file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
    "void ${init}(py::module_ &);\n")
endforeach()

file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
  "\n\n/**
   @brief Creates IgANet Python module
*/

PYBIND11_MODULE(pyiganet_core, m) {\n

m.attr(\"__name__\") = \"pyiganet_core\";
m.attr(\"__version__\") = \"${IGANET_VERSION}\";
m.doc() = \"IgANet (Physics-informed isogeometric analysis neural network)\";

py::module core = m.def_submodule(\"core\");

core.attr(\"__name__\") = \"pyiganet_core.core\";
core.attr(\"__version__\") = \"${IGANET_VERSION}\";
core.doc() = \"IgANet (Physics-informed isogeometric analysis neural network): Core module\";

")

foreach(init IN LISTS init_core)
  file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
    "${init}(core);\n")
endforeach()

file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
  "\n

py::module splines = m.def_submodule(\"splines\");

splines.attr(\"__name__\") = \"pyiganet_core.splines\";
splines.attr(\"__version__\") = \"${IGANET_VERSION}\";
splines.doc() = \"IgANet (Physics-informed isogeometric analysis neural network): Spline module\";

")

foreach(init IN LISTS init_splines)
  file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
    "${init}(splines);\n")
endforeach()

file(APPEND ${PROJECT_BINARY_DIR}/pyiganet/csrc/pyiganet.cxx
    "}\n")

file(GLOB SRCS ${PROJECT_SOURCE_DIR}/pyiganet/csrc/*.cxx ${PROJECT_BINARY_DIR}/pyiganet/csrc/*.cxx)

pybind11_add_module(pyiganet_core MODULE ${SRCS})
target_link_libraries(pyiganet_core PRIVATE iganet::core)
target_link_libraries(pyiganet_core PRIVATE iganet::python)
