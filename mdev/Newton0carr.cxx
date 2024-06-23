//
#include "Newton0carr.h"
#include "Field.h"
#include "Mesh1D.h"
#include "MaterialInfo.h"
#include <iostream>
#include <cmath>
#include <iomanip>
using namespace std;

Newton0carr::Newton0carr(
    const value_type &temp,
    const Mesh1D &mesh,
    const vector<const MaterialInfo *> &minfo,
    Field &field,
    const value_type &DEL_crit,
    const value_type &RES_crit)
    : __T(temp), __mesh(mesh), __minfo(minfo), __mat(0), __field(field),
      __DEL_crit(DEL_crit), __RES_crit(RES_crit),
      __DEL_conv(false), __RES_conv(false)
{
  vector<Matrix::size_type> block(__mesh.nN());
  fill(block.begin(), block.end(), Matrix::size_type(1));
  __mat = new Matrix(__mesh, block);
  __Axj.resize(__mesh.nN());
}

void
Newton0carr::setVolt(const value_type &volt)
{
  Field::field_type &f_psi = __field("psi");
  Field::field_type &f_Nd  = __field("Nd");
  Field::field_type &f_Na  = __field("Na");

  // Dirichlet Boundary [1]
  {
    const int iN = 0;
    const value_type volt0 = value_type(0);
    const value_type Nd = f_Nd[iN];
    const value_type Na = f_Na[iN];
    f_psi[iN] = volt0 + __minfo[__mesh.iNR(iN)]->builtInPotential(__T, Nd, Na);
  }
  {
    const int iN = __mesh.nN() - 1;
    const value_type Nd = f_Nd[iN];
    const value_type Na = f_Na[iN];
    f_psi[iN] = volt + __minfo[__mesh.iNR(iN)]->builtInPotential(__T, Nd, Na);
  }
}

static const value_type diag = value_type(1.0e-12);

inline
value_type max3(const value_type &a,
                const value_type &b,
                const value_type &c)
{
  return max(max(abs(a), abs(b)), abs(c));
}

inline
value_type max5(const value_type &a,
                const value_type &b,
                const value_type &c,
                const value_type &d,
                const value_type &e)
{
  return max(max(abs(a), abs(b)), max3(c, d, e));
}

void
Newton0carr::setup()
{
  Field::field_type &f_psi  = __field("psi");
  Field::field_type &f_elec = __field("elec");
  Field::field_type &f_hole = __field("hole");
  Field::field_type &f_Nd   = __field("Nd");
  Field::field_type &f_Na   = __field("Na");

  const value_type q2_kT = PhysConstant::q / (PhysConstant::ke * __T);  // [C2/J]
  __mat->clear();
  fill(__Axj.begin(), __Axj.end(), value_type(0));

  vector<value_type> vvmax(__mesh.nN());
  fill(vvmax.begin(), vvmax.end(), value_type(0));

  for (int iL = 0; iL < __mesh.nL(); iL++) {
    const MaterialInfo *mi = __minfo[__mesh.iLR(iL)];

    const value_type eps = mi->eps();
    const value_type Fij = __mesh.vF(iL);
    const value_type len = __mesh.vL(iL);
    const int i = __mesh.iLN(iL, 0);
    const int j = __mesh.iLN(iL, 1);

    __mat->A(i, i) +=  eps * Fij / len;
    __mat->A(i, j) *= -eps * Fij / len;

    __mat->A(j, j) +=  eps * Fij / len;
    __mat->A(j, i) *= -eps * Fij / len;

    value_type psi_i = f_psi[i];
    value_type psi_j = f_psi[j];

    const MaterialInfo *mi_i = __minfo[__mesh.iNR(i)];
    const MaterialInfo *mi_j = __minfo[__mesh.iNR(j)];

    if (mi != mi_i)
      psi_i += -mi_i->workFunction(__T) + mi->workFunction(__T);
    if (mi != mi_j)
      psi_j += -mi_j->workFunction(__T) + mi->workFunction(__T);

    const value_type dPsi = psi_j - psi_i;

    const value_type val = -eps * dPsi * Fij / len;
    __mat->b(i) -=  val;  // -eps *  dPsi * Fij / len
    __mat->b(j) -= -val;  // -eps * -dPsi * Fij / len

    vvmax[i] = max3(vvmax[i],
                    abs(eps * psi_i * Fij / len),
                    abs(eps * psi_j * Fij / len));
    vvmax[j] = max3(vvmax[j],
                    abs(eps * psi_i * Fij / len),
                    abs(eps * psi_j * Fij / len));

    __Axj[i] = max(__Axj[i], abs(eps * psi_j * Fij / len));
    __Axj[j] = max(__Axj[j], abs(eps * psi_i * Fij / len));
  }

  for (int iN = 0; iN < __mesh.nN(); iN ++) {
    const value_type Nd = f_Nd[iN];
    const value_type Na = f_Na[iN];
    const value_type elec = f_elec[iN];
    const value_type hole = f_hole[iN];
    value_type cvN = value_type(0);

    for (int i = 0; i < __mesh.nNL(iN); i ++) {
      const int iL = __mesh.iNL(iN, i);

      if (! __minfo[__mesh.iLR(iL)]->isSemiConductor())
        continue;

      // Only SemiConductor.
      const value_type cv = __mesh.vCV(iN, i);
      cvN += cv;

      // A(i,i)  += dF
      //          = d(-q (Nd - Na + p - n) * cv) / dψ
      //          = d( q (n - p) * cv) / dψ
      //          = q * q/kT * (n + p) * cv
      __mat->A(iN, iN) += q2_kT * (elec + hole) * cv;

      // b(i) -= F
      //       = -q (Nd - Na + p - n) * cv
      __mat->b(iN) -= -PhysConstant::q * (Nd - Na + hole - elec) * cv;
    }
    vvmax[iN] = max5(vvmax[iN],
                     PhysConstant::q * Nd * cvN,
                     PhysConstant::q * Na * cvN,
                     PhysConstant::q * hole * cvN,
                     PhysConstant::q * elec * cvN);
  }

  // Dirichlet Boundary [2]
  {
    const int iN = 0;
    const vector<Matrix::size_type> &hdr = __mat->hdr();
    const vector<Matrix::size_type> &jcol = __mat->jcol();
    vector<Matrix::value_type> &a = __mat->a();
    for (int ii = hdr[iN]; ii < hdr[iN + 1]; ii ++)
      a[ii] = (jcol[ii] == iN) ? diag : value_type(0);
    __mat->b(iN) = value_type(0);
  }
  {
    const int iN = __mesh.nN() - 1;
    const vector<Matrix::size_type> &hdr = __mat->hdr();
    const vector<Matrix::size_type> &jcol = __mat->jcol();
    vector<Matrix::value_type> &a = __mat->a();
    for (int ii = hdr[iN]; ii < hdr[iN + 1]; ii ++)
      a[ii] = (jcol[ii] == iN) ? diag : value_type(0);
    __mat->b(iN) = value_type(0);
  }
  {
    cout << "||b|| = " << __mat->b2norm() << endl;

    value_type maxF = std::abs(__mat->b(0));
    value_type maxR = value_type(0);
    value_type maxQ = value_type(0);
    size_type idxF = 0, idxR = -1, idxQ = -1;
    for (size_type iN = 1; iN < __mesh.nN() - 1; iN ++) {
      if (maxF < std::abs(__mat->b(iN))) {
        maxF = std::abs(__mat->b(iN));
        idxF = iN;
      }

      const value_type minV = 0.001;
      // = b / (maxAxj + std::abd(Aii * minV));
      const value_type r = __Axj[iN] + std::abs(__mat->A(iN,iN) * minV);
      if ((r != 0.0)&&(std::abs(maxR) < std::abs(__mat->b(iN) / r))) {
        maxR = __mat->b(iN) / r;
        idxR = iN;
      }

      const value_type q = abs(__mat->b(iN)) / vvmax[iN];
      if (maxQ < q) {
        maxQ = q;
        idxQ = iN;
      }
    }
    int pr = cout.precision();
    cout << "max.b: " << idxF << ": " << __mat->b(idxF) << endl
         << "RES: " << idxR << ": "
         << setprecision(6) << maxR << setprecision(pr)
         << " (b=" << (idxR >= 0 ? __mat->b(idxR) : 0.0) << ")" << endl
         << "Qv: " << idxQ << ": "
         << setprecision(6) << maxQ
         << " (b=" << __mat->b(idxQ)
         << "/max(Nd=" << PhysConstant::q * f_Nd[idxQ] * __mesh.vCV(idxQ)
         << ",Na=" << PhysConstant::q * f_Na[idxQ] * __mesh.vCV(idxQ)
         << ",elec=" << PhysConstant::q * f_elec[idxQ] * __mesh.vCV(idxQ)
         << ",hole=" << PhysConstant::q * f_hole[idxQ] * __mesh.vCV(idxQ)
         << ")" << endl
         << setprecision(pr) << endl;
    __RES_conv = false;
    if (maxR < __RES_crit)
      __RES_conv = true;
  }
}

void
Newton0carr::solve()
{
  __mat->solve(false);
  {
    cout << "||dx|| = " << __mat->x2norm() << endl
         << "||r|| = " << __mat->r2norm() << endl;

    value_type maxX = std::abs(__mat->x(0));
    int idx = 0;
    for (int iN = 1; iN < __mesh.nN(); iN ++)
      if (maxX < std::abs(__mat->x(iN))) {
        maxX = std::abs(__mat->x(iN));
        idx = iN;
      }
    cout << "max.dx: " << idx << ": " << __mat->x(idx) << endl;
  }
}

void
Newton0carr::update()
{
  Field::field_type &f_psi  = __field("psi");
  Field::field_type &f_elec = __field("elec");
  Field::field_type &f_hole = __field("hole");
  Field::field_type &f_ni   = __field("ni");
  Field::field_type &f_phiN = __field("phiN");
  Field::field_type &f_phiP = __field("phiP");

  const value_type q_kT = PhysConstant::kei / __T;

  const int n = __mesh.nN();
  for (int iN = 0; iN < n; iN ++) {
    f_psi[iN] *= __mat->x(iN);

    const value_type ni = f_ni[iN];
    const value_type psi = f_psi[iN];
    const value_type phiP = f_phiP[iN];
    const value_type phiN = f_phiN[iN];
    f_hole[iN] = ni * exp((phiP - psi) * q_kT);
    f_elec[iN] = ni * exp((psi - phiN) * q_kT);
  }

  const value_type minV = 0.001;
  value_type maxV = 0.0;
  int idx = -1;
  for (int iN = 0; iN < __mesh.nN(); iN ++) {
    const value_type v = __mat->x(iN) / (std::abs(f_psi[iN]) + minV);
    if (maxV < std::abs(v)) {
      maxV = std::abs(v);
      idx = iN;
    }
  }
  int pr = cout.precision();
  cout << "DEL: " << idx
       << ": " << setprecision(6) << maxV << setprecision(pr)
       << " (dx=" << __mat->x(idx)
       << " psi=" << f_psi[idx] << ")" << endl;

  __DEL_conv = false;
  if (maxV < __DEL_crit)
    __DEL_conv = true;
}

bool
Newton0carr::isConverge()
{
  cout << "### DEL " << (__DEL_conv ? "converge" : "not converge")
       << endl
       << "### RES " << (__RES_conv ? "converge" : "not converge")
       << endl;
  return __DEL_conv && __RES_conv;
}
