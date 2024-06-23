// -*- c++ -*-
#ifndef NEWTON_0CARR_H_
#define NEWTON_0CARR_H_

#include "NewtonIF.h"
#include "Matrix.h"
#include "ValueType.h"

class Mesh1D;
class Field;
class MaterialInfo;

#include <vector>

class Newton0carr: public NewtonIF {
 private:
  value_type __T;
  const Mesh1D &__mesh;
  const std::vector<const MaterialInfo *> &__minfo;
  Matrix *__mat;
  Field &__field;
  std::vector<value_type> __Axj;

  const value_type __DEL_crit, __RES_crit;
  bool __DEL_conv, __RES_conv;

 public:
  Newton0carr(const value_type &temp,
              const Mesh1D &mesh,
              const std::vector<const MaterialInfo *> &minfo,
              Field &field,
              const value_type &DEL_crit,
              const value_type &RES_crit);
  virtual ~Newton0carr() { delete __mat; }

  void setup();
  void solve();
  void update();
  bool isConverge();
  void setVolt(const value_type &volt);
};

#endif // NEWTON_0CARR_H_
