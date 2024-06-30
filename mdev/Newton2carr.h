// -*- c++ -*-
#ifndef NEWTON_2CARR_H_
#define NEWTON_2CARR_H_

#include "NewtonIF.h"
#include "Matrix.h"
#include "ValueType.h"

class Mesh1D;
class Field;
class MaterialInfo;

#include <vector>

class Newton2carr: public NewtonIF {
 private:
  value_type __T;
  const Mesh1D &__mesh;
  const std::vector<const MaterialInfo *> &__minfo;
  Matrix *__mat;
  Field &__field;
  std::vector<Matrix::size_type> __block;
  std::vector<value_type> __Axj;

  const value_type __DEL_crit, __RES_crit;
  bool __DEL_conv, __RES_conv;

 public:
  Newton2carr(const value_type &temp,
              const Mesh1D &mesh,
              const std::vector<const MaterialInfo *> &minfo,
              Field &field,
              const value_type &DEL_crit,
              const value_type &RES_crit);
  virtual ~Newton2carr() { delete __mat; }

  void setup();
  void solve();
  void update();
  bool isConverge();
  void setVolt(const value_type &volt);
};

#endif // NEWTON_2CARR_H_
