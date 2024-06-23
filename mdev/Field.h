// -*- c++ -*-
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#ifndef FIELD_H_
#define FIELD_H_

#include "ValueType.h"
#include <map>
#include <vector>
#include <string>

class MaterialInfo;
class Recipe;
class Mesh1D;

class Field {
public:
  typedef std::vector<value_type> field_type;

private:
  std::map<std::string, field_type> __f;

public:
  Field (value_type temp, const std::vector<Recipe> &devicerecipes,
         const Mesh1D &mesh, const std::vector<const MaterialInfo *> &minfo);

  const field_type
  &operator() (const std::string &name) const { return __f.at(name); }

  field_type
  &operator() (const std::string &name) { return __f.at(name); }

  void output (const std::string &name, const std::string &fname = "") const;
};

#endif  // FIELD_H_
