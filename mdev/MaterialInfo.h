// -*- c++ -*-
#ifndef _MATERIAL_INFO__H
#define _MATERIAL_INFO__H

#include "ValueType.h"
#include <cmath>

namespace PhysConstant {
  static const value_type q = 1.6021892e-19L; // 電気素量 [C]
  static const value_type k = 1.380662e-23L;  // ボルツマン定数 [J/K] *MSK
  static const value_type T0 = 300.0L;        // [K]
  static const value_type ke = k / q;
  static const value_type kei = q / k;
  static const value_type eps0 = 8.854187818e-14L; // 真空誘電率 [F/cm]
  // -------------------------------------------------------------------
  // F = C/V = s4A2/(m2kg) = 1e-7 s4A2 / (cm2*g)
  // C = A s
  // V = W/A = J/C = J/(A s)
  // W = J/s
  // J = N m = kg m2 / s2 = 1e7 g cm2 / s2
  // -------------------------------------------------------------------
}

class MaterialInfo {
public:
  MaterialInfo () {}
  virtual ~MaterialInfo () {}

  virtual int priority () const = 0;
  virtual bool isSemiConductor () const = 0;

  virtual value_type eps () const = 0;
  virtual value_type elec_mu0 () const { return 0.0L; }
  virtual value_type hole_mu0 () const { return 0.0L; }

  virtual value_type elecAffinity () const = 0;
  virtual value_type effectDensStateValence (const value_type &temp) const {
    const value_type T = temp / PhysConstant::T0;
    return 1.04e19L * T * sqrt (T);
  }
  virtual value_type effectDensStateConduction (const value_type &temp) const {
    const value_type T = temp / PhysConstant::T0;
    return 2.8e19L * T * sqrt (T);
  }
  virtual value_type bandGapEnergy (const value_type &temp) const {
    return 0.0L;
  }
  virtual value_type bandGapNarrowing (const value_type &donor,
				       const value_type &acceptor) const {
    return 0.0L;
  }
  virtual value_type carrConc (const value_type &temp,
			       const value_type &dEg = 0.0) const {
    return 0.0L;
  }
  virtual value_type builtInPotential (const value_type &temp,
				       const value_type &donor,
				       const value_type &acceptor) const {
    return 0.0L;
  }
  virtual value_type intrinsicFermiLevel (const value_type &temp) const {
    const value_type Eg = bandGapEnergy(temp);
    const value_type Nc = effectDensStateConduction(temp);
    const value_type Nv = effectDensStateValence(temp);
    return (Eg + PhysConstant::ke * temp * log(Nc/Nv)) * 0.5L;
  }
  virtual value_type workFunction (const value_type &temp) const {
    const value_type chi = elecAffinity ();
    const value_type Efi = intrinsicFermiLevel (temp);
    return Efi + chi;
  }
};

#endif // ! _MATERIAL_INFO__H
